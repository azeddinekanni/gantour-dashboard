"""
Onglet "Veille marche & Agent IA" du dashboard OCP Gantour Intelligence.
Appel depuis app.py : market_tab.render(mines_df, {"UC": uc_df, "US": us_df, "UL": ul_df}, PHASE_LABELS)
"""
import json
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ai_agent
import alerts
import market_data
import signals
from market_data import INDICATORS
from style import style_plotly

FP_PATH = market_data.DATA_DIR / "agent_state.json"

NIVEAU_STYLE = {
    "stable": ("Marche stable", "#00E676"),
    "surveillance": ("Sous surveillance", "#FFB020"),
    "tension": ("Tension", "#FF5C5C"),
}
PRIO_COLOR = {"haute": "#FF5C5C", "moyenne": "#FFB020", "basse": "#00E676"}

CSS = """
<style>
.mk-card{background:var(--ocp-panel);border:1px solid var(--ocp-line);border-radius:16px;
  padding:18px 16px;text-align:center;height:100%;}
.mk-card.alert{border-color:rgba(255,92,92,0.45);}
.mk-icon{font-size:30px;line-height:1;}
.mk-name{font-weight:800;font-size:13px;letter-spacing:0.6px;margin-top:10px;color:#EAF7F0;}
.mk-sub{font-size:11px;color:var(--ocp-muted);margin-top:2px;min-height:28px;}
.mk-value{font-size:28px;font-weight:800;margin-top:6px;color:#F3FFF8;}
.mk-unit{font-size:11px;color:var(--ocp-muted);}
.mk-chips{display:flex;gap:6px;justify-content:center;flex-wrap:wrap;margin-top:10px;}
.mk-chip{font-size:11px;font-weight:700;border-radius:20px;padding:3px 10px;border:1px solid;}
.mk-foot{font-size:10.5px;color:var(--ocp-muted);margin-top:8px;}
.mk-summary{background:var(--ocp-panel);border:1px solid var(--ocp-line);border-radius:16px;padding:20px 22px;}
.mk-summary p{font-size:15px;line-height:1.55;margin:0;}
.mk-src{display:inline-block;font-size:11px;font-weight:700;background:var(--ocp-panel-2);
  border-radius:20px;padding:3px 10px;margin-right:6px;margin-top:10px;}
.mk-rec{background:var(--ocp-panel-2);border-left:4px solid;border-radius:12px;padding:14px 16px;margin-bottom:10px;}
.mk-rec-title{font-weight:800;font-size:14px;}
.mk-rec-body{font-size:13px;margin-top:6px;line-height:1.5;}
.mk-rec-why{font-size:12px;color:var(--ocp-muted);margin-top:6px;}
.mk-change{background:rgba(255,176,32,0.10);border:1px solid rgba(255,176,32,0.45);border-radius:12px;
  padding:10px 14px;font-size:13px;color:#FFE1A8;margin-bottom:12px;}
</style>
"""


def _fmt(v, unit):
    if v is None:
        return "n.d."
    return f"{v:,.2f}".replace(",", " ") if unit != "Indice" else f"{v:,.1f}".replace(",", " ")


def _load_state():
    try:
        return json.loads(FP_PATH.read_text())
    except Exception:
        return {}


def _save_state(state):
    try:
        FP_PATH.parent.mkdir(parents=True, exist_ok=True)
        FP_PATH.write_text(json.dumps(state))
    except Exception:
        pass


def _indicator_card(sig):
    meta = INDICATORS[sig["cle"]]
    niveau_txt, niveau_col = NIVEAU_STYLE[sig["niveau"]]
    mom = sig["variation_mensuelle_pct"] or 0
    mom_col = "#FF5C5C" if sig["defavorable"] else "#00E676"
    freq = sig["frequence_hist_hausse_mois_suivant_pct"]
    foot = (f"Hausse le mois suivant dans {freq:.0f} % des cas comparables (n = {sig['nb_cas_comparables']})"
            if freq is not None else "Historique insuffisant pour une frequence fiable")
    alert_cls = " alert" if sig["defavorable"] and sig["niveau"] == "tension" else ""
    st.markdown(
        f"""<div class="mk-card{alert_cls}">
            <div class="mk-icon">{meta['icon']}</div>
            <div class="mk-name">{sig['libelle']}</div>
            <div class="mk-sub">{meta['sub']}</div>
            <div class="mk-value">{_fmt(sig['derniere_valeur'], sig['unite'])}</div>
            <div class="mk-unit">{sig['unite']} &#183; {sig['date_derniere_valeur']}</div>
            <div class="mk-chips">
                <span class="mk-chip" style="color:{mom_col};border-color:{mom_col}66;background:{mom_col}14;">{mom:+.1f} % sur 1 mois</span>
                <span class="mk-chip" style="color:{niveau_col};border-color:{niveau_col}66;background:{niveau_col}14;">&#9679; {niveau_txt}</span>
            </div>
            <div class="mk-foot">{foot}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _health_gauge(health):
    color = "#00E676" if health["score"] >= 75 else ("#FFB020" if health["score"] >= 50 else "#FF5C5C")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=health["score"],
        number={"suffix": " /100", "font": {"size": 34, "color": color}},
        gauge={"axis": {"range": [0, 100], "tickcolor": "#8DA69C"},
               "bar": {"color": color, "thickness": 0.3},
               "bgcolor": "#17221D", "borderwidth": 0,
               "steps": [{"range": [0, 50], "color": "rgba(255,92,92,0.10)"},
                         {"range": [50, 75], "color": "rgba(255,176,32,0.10)"},
                         {"range": [75, 100], "color": "rgba(0,230,118,0.10)"}]},
    ))
    fig.update_layout(height=230, margin=dict(t=20, b=0, l=20, r=20))
    return style_plotly(fig)


def render(mines_df, phase_dfs, phase_labels):
    st.markdown(CSS, unsafe_allow_html=True)

    top_l, top_r = st.columns([4, 1])
    with top_l:
        st.markdown("#### Veille marche et recommandations de l'agent IA")
        st.caption("Les chiffres sont calcules par le moteur de signaux ; l'agent IA redige uniquement "
                   "l'interpretation et les recommandations a partir de ces chiffres.")
    with top_r:
        if st.button("Actualiser les donnees", use_container_width=True, key="mk_refresh"):
            market_data.get_market_data.clear()
            ai_agent.generate_insights.clear()
            st.rerun()

    with st.spinner("Recuperation des prix de marche..."):
        market_df, status = market_data.get_market_data()

    ind = signals.compute_indicator_signals(market_df)
    internal = signals.internal_signals(mines_df, phase_dfs, phase_labels)
    health = signals.health_score(ind, internal)
    context = signals.build_context(ind, internal, health)
    fp = signals.fingerprint(ind, internal)

    if not ind:
        st.warning("Aucune donnee de marche disponible. Verifiez la connexion Internet ou placez le fichier "
                   "Pink Sheet dans data/market/ (voir la documentation du module market_data).")
        return

    # Detection de changement depuis la derniere analyse
    state = _load_state()
    if state.get("fingerprint") and state["fingerprint"] != fp:
        st.markdown(
            f'<div class="mk-change">Changement detecte depuis la derniere analyse du '
            f'{state.get("date", "?")} : l\'agent a regenere ses recommandations.</div>',
            unsafe_allow_html=True,
        )
    if state.get("fingerprint") != fp:
        _save_state({"fingerprint": fp, "date": datetime.now().strftime("%d/%m/%Y %H:%M")})

    with st.spinner("Analyse de l'agent IA..."):
        insights = ai_agent.generate_insights(fp, context)

    # ---------- Synthese
    sources = sorted({INDICATORS[k]["source"] for k, v in status.items() if v != "indisponible"})
    moteur = "Gemini" if insights["moteur"] == "gemini" else "Moteur de regles (agent IA indisponible)"
    st.markdown(
        f"""<div class="mk-summary">
            <p>{insights.get('synthese', '')}</p>
            <p style="margin-top:10px;font-size:13px;color:var(--ocp-muted);">
                Risque principal : <b style="color:#FFB020;">{insights.get('risque_principal', 'n.d.')}</b></p>
            <div>{''.join(f'<span class="mk-src">{s}</span>' for s in sources)}
                <span class="mk-src" style="color:var(--ocp-muted);">Analyse : {moteur}</span></div>
        </div>""",
        unsafe_allow_html=True,
    )
    if insights.get("erreur"):
        st.caption(f"Detail technique de l'agent : {insights['erreur']}")
    unavailable = [INDICATORS[k]["label"] for k, v in status.items() if v == "indisponible"]
    if unavailable:
        st.caption("Series indisponibles : " + ", ".join(unavailable))
    st.markdown("")

    # ---------- Cartes indicateurs (couts d'abord, puis valorisation)
    ordered = sorted(ind, key=lambda s: (s["role"] != "cout", s["cle"] == "acide_sulf"))
    for start in range(0, len(ordered), 4):
        cols = st.columns(4)
        for col, sig in zip(cols, ordered[start:start + 4]):
            with col:
                _indicator_card(sig)
        st.markdown("")

    # ---------- Score + recommandations
    col_score, col_recs = st.columns([1, 2])
    with col_score:
        with st.container(border=True):
            st.markdown("##### Score de sante des couts")
            st.plotly_chart(_health_gauge(health), use_container_width=True)
            st.markdown(f"**Niveau : {health['niveau']}**")
            with st.expander("Detail du calcul"):
                st.caption("100 moins les penalites : indicateur de cout defavorable en tension -12, "
                           "en surveillance -6 ; cout unitaire interne +10 % sur 30 j -12, +5 % -6.")
                if health["penalites"]:
                    for p in health["penalites"]:
                        st.write(f"- {p}")
                else:
                    st.write("Aucune penalite.")
    with col_recs:
        with st.container(border=True):
            st.markdown("##### Recommandations")
            for r in insights.get("recommandations", []):
                color = PRIO_COLOR.get(r.get("priorite", "basse"), "#8DA69C")
                liens = ", ".join(r.get("indicateurs_lies", []))
                st.markdown(
                    f"""<div class="mk-rec" style="border-color:{color};">
                        <div class="mk-rec-title"><span style="color:{color};">Priorite {r.get('priorite', '')}</span>
                            &nbsp;{r.get('titre', '')}</div>
                        <div class="mk-rec-body">{r.get('action', '')}</div>
                        <div class="mk-rec-why">{r.get('justification', '')}{' (' + liens + ')' if liens else ''}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            if insights.get("points_de_vigilance"):
                with st.expander("Points de vigilance"):
                    for p in insights["points_de_vigilance"]:
                        st.write(f"- {p}")

    # ---------- Indicateurs internes
    with st.container(border=True):
        st.markdown("##### Indicateurs internes Gantour (30 derniers jours vs 30 jours precedents)")
        df_int = pd.DataFrame(internal).rename(columns={
            "perimetre": "Perimetre", "type": "Type",
            "cout_unitaire_30j_dh_t": "Cout unitaire (DH/t)",
            "variation_cout_unitaire_pct": "Var. cout unitaire (%)",
            "production_30j_t": "Production (t)",
            "variation_production_pct": "Var. production (%)",
            "date_derniere_donnee": "Derniere donnee",
        })
        st.dataframe(df_int, use_container_width=True, hide_index=True)

    # ---------- Historique d'un indicateur
    with st.container(border=True):
        st.markdown("##### Historique d'un indicateur de marche")
        key = st.selectbox("Indicateur", [s["cle"] for s in ordered],
                           format_func=lambda k: INDICATORS[k]["label"], key="mk_hist")
        s = market_data.series_for(market_df, key).iloc[-48:]
        roll = s.rolling(12).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=s.index, y=s.values, name=INDICATORS[key]["label"],
                                 line=dict(color="#00E676")))
        fig.add_trace(go.Scatter(x=roll.index, y=roll.values, name="Moyenne mobile 12 mois",
                                 line=dict(color="#FFB020", dash="dash")))
        fig.update_layout(height=320, yaxis_title=INDICATORS[key]["unit"],
                          margin=dict(t=10, l=10, r=10, b=10), legend_title_text="")
        st.plotly_chart(style_plotly(fig), use_container_width=True)

    # ---------- Question libre a l'agent
    with st.container(border=True):
        st.markdown("##### Poser une question a l'agent")
        q = st.text_input("Question", placeholder="Ex. Quel site est le plus expose a la hausse du gasoil ?",
                          label_visibility="collapsed", key="mk_question")
        if st.button("Envoyer la question", key="mk_ask") and q.strip():
            with st.spinner("L'agent reflechit..."):
                st.session_state.mk_answer = ai_agent.ask_agent(q.strip(), context)
        if st.session_state.get("mk_answer"):
            st.info(st.session_state.mk_answer)

    # ---------- Diffusion aux managers
    with st.expander("Envoyer la synthese aux managers"):
        recipients_raw = st.text_input("Emails (separes par une virgule)",
                                       value="manager.gantour@ocpgroup.ma", key="mk_recipients")
        if st.button("Envoyer la synthese", key="mk_send"):
            recs_txt = "\n".join(f"- [{r.get('priorite', '')}] {r.get('titre', '')} : {r.get('action', '')}"
                                 for r in insights.get("recommandations", []))
            body = (f"Bonjour,\n\nSynthese de la veille marche du {datetime.now():%d/%m/%Y} :\n\n"
                    f"{insights.get('synthese', '')}\n\nScore de sante : {health['score']}/100 ({health['niveau']})\n\n"
                    f"Recommandations :\n{recs_txt}\n\n"
                    f"Message genere par OCP Gantour Intelligence.")
            subject = f"[OCP GANTOUR] Veille marche - score {health['score']}/100"
            recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
            ok, msg = alerts.send_email_alert(recipients, subject, body)
            (st.success if ok else st.warning)(msg)
