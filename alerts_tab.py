"""
Onglet "Objectifs & Alertes" du dashboard OCP Gantour Intelligence.
Appel depuis app.py :
    alerts_tab.render(mines_df, {"UC": uc_df, "US": us_df, "UL": ul_df},
                      MINE_LABELS, PHASE_LABELS, MINE_VAR_LABELS,
                      PHASE_VAR_LABELS_UC_US, PHASE_VAR_LABELS_UL)
"""
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import ai_agent
import alerts
import style
from style import style_plotly

PERIODES = {"30 jours": 30, "90 jours": 90, "1 an": 365, "Tout": None}


def _unit_from_label(label):
    m = re.search(r"\(([^)]*)\)\s*$", label)
    return m.group(1) if m else ""


def _alert_chart(df, var, label, limit, mode, demo_point=None):
    d = df[["date", var]].dropna().sort_values("date")
    hors_seuil = d[var] > limit if mode == "max" else d[var] < limit
    colors = ["#FF5C5C" if h else "#00C97A" for h in hors_seuil]
    moyenne_7j = d[var].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=d["date"], y=d[var], name="Valeur journaliere",
                         marker_color=colors, opacity=0.85,
                         hovertemplate="%{x|%d/%m/%Y}<br>%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=d["date"], y=moyenne_7j, name="Moyenne mobile 7 jours",
                             line=dict(color="#FFB020", width=2.5)))
    fig.add_hline(y=limit, line_dash="dash", line_color="#FF5C5C", line_width=2,
                  annotation_text="Objectif minimum" if mode == "min" else "Limite maximale",
                  annotation_font_color="#FF5C5C")
    if demo_point is not None:
        fig.add_trace(go.Scatter(x=[demo_point[0]], y=[demo_point[1]], mode="markers",
                                 name="Valeur saisie (demonstration)",
                                 marker=dict(size=14, color="#FFFFFF", line=dict(color="#FF5C5C", width=3))))
    fig.update_layout(height=340, bargap=0.15, margin=dict(t=30, l=10, r=10, b=10),
                      yaxis_title=label, legend=dict(orientation="h", y=1.12, x=0),
                      hovermode="x unified")
    return style_plotly(fig), int(hors_seuil.sum()), len(d)


def render(mines_df, phase_dfs, mine_labels, phase_labels,
           mine_var_labels, phase_var_labels_uc_us, phase_var_labels_ul):

    with st.container(border=True):
        st.markdown("#### Objectifs de production et limites de consommation")
        st.caption("Definissez une limite journaliere (ou un objectif minimum de production) pour un site ou une phase. "
                   "Le tableau de bord compare la derniere valeur enregistree a ce seuil et envoie un email aux "
                   "destinataires en cas de depassement, avec des recommandations.")

        # ---------- Configuration email
        if alerts.email_config_ok():
            st.markdown('<span class="badge badge-normal"><span class="badge-dot"></span>'
                        'Envoi d\'emails configure</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-critique"><span class="badge-dot"></span>'
                        'Envoi d\'emails non configure (ALERT_EMAIL_SENDER / ALERT_EMAIL_PASSWORD manquants)'
                        '</span>', unsafe_allow_html=True)
        st.markdown("")

        # ---------- Choix du perimetre et de la variable
        c1, c2, c3 = st.columns(3)
        with c1:
            scope = st.radio("Perimetre", ["Mines d'extraction", "Phases de traitement"],
                             horizontal=True, key="alert_scope")
        if scope == "Mines d'extraction":
            with c2:
                code = st.selectbox("Site", list(mine_labels.keys()),
                                    format_func=lambda x: mine_labels[x], key="alert_site")
            df_alert = mines_df[mines_df["mines"] == code]
            labels = mine_var_labels
            site_label = mine_labels[code]
        else:
            with c2:
                code = st.selectbox("Phase", list(phase_dfs.keys()),
                                    format_func=lambda x: phase_labels[x], key="alert_phase")
            df_alert = phase_dfs[code]
            labels = phase_var_labels_ul if code == "UL" else phase_var_labels_uc_us
            site_label = phase_labels[code]
        with c3:
            var = st.selectbox("Variable a surveiller", list(labels.keys()),
                               format_func=lambda x: labels[x], key="alert_var")

        var_label = labels[var]
        unit = _unit_from_label(var_label)
        mode = "min" if "production" in var else "max"
        serie = df_alert[["date", var]].dropna().sort_values("date")
        if serie.empty:
            st.warning("Aucune donnee disponible pour cette variable.")
            return

        hist_mean = serie[var].mean()
        hist_p90 = serie[var].quantile(0.9)
        hist_p10 = serie[var].quantile(0.1)

        col_cfg, col_status = st.columns([1, 1.4])

        # ---------- Configuration du seuil et des destinataires
        with col_cfg:
            st.markdown("##### Seuil et destinataires")
            default_limit = float(hist_p90 if mode == "max" else hist_p10)
            limit = st.number_input(
                f"{'Objectif minimum' if mode == 'min' else 'Limite journaliere maximale'} ({unit or var_label})",
                value=round(default_limit, 2), min_value=0.0, step=100.0,
                key=f"alert_limit_{scope}_{code}_{var}",  # une valeur memorisee par site et par variable
            )
            st.caption(f"Reperes historiques : moyenne {hist_mean:,.0f} - 10e centile {hist_p10:,.0f} - "
                       f"90e centile {hist_p90:,.0f}")

            recipients_raw = st.text_input("Emails des destinataires (separes par une virgule)",
                                           value=st.session_state.get("alert_recipients_default", ""),
                                           placeholder="prenom.nom@ocpgroup.ma, autre@gmail.com",
                                           key="alert_recipients")
            recipients, invalid = alerts.parse_recipients(recipients_raw)
            if invalid:
                st.error("Adresse(s) invalide(s) : " + ", ".join(invalid))

            auto_send = st.toggle("Envoi automatique des qu'un depassement est detecte", value=True,
                                  key="alert_auto")
            with_ai = st.toggle("Inclure les recommandations de l'agent IA", value=True, key="alert_ai")

            with st.expander("Mode demonstration : saisir la valeur du jour"):
                st.caption("Simule la reception d'une nouvelle valeur pour tester le declenchement de l'alerte "
                           "devant un public, sans modifier les donnees.")
                demo_on = st.checkbox("Utiliser une valeur saisie", key="alert_demo_on")
                demo_value = st.number_input("Valeur du jour", value=float(round(hist_p90 * 1.15, 0)),
                                             min_value=0.0, step=100.0, key=f"alert_demo_{code}_{var}")

        # ---------- Valeur courante
        if demo_on:
            current_value = float(demo_value)
            current_date = pd.Timestamp.today().normalize()
            demo_point = (current_date, current_value)
        else:
            last = serie.iloc[-1]
            current_value = float(last[var])
            current_date = last["date"]
            demo_point = None

        status, ratio = alerts.evaluate_threshold(current_value, limit, mode=mode)
        date_str = current_date.strftime("%d/%m/%Y")

        # ---------- Etat et graphe
        with col_status:
            st.markdown("##### Etat actuel")
            banner_cls = "critique" if status == "critique" else ("vigilance" if status in ("vigilance", "alerte") else "normal")
            st.markdown(
                f'<div class="alert-banner alert-{banner_cls}">{site_label} - {var_label} : '
                f'{current_value:,.0f} {unit} le {date_str}{" (valeur saisie)" if demo_on else ""}<br>'
                f'<span style="font-weight:500;">Seuil : {limit:,.0f} {unit} - soit {ratio * 100:,.0f} % du seuil</span></div>',
                unsafe_allow_html=True,
            )
            style.badge(status, alerts.STATUS_LABELS.get(status, status))

            periode = st.radio("Periode affichee", list(PERIODES.keys()), index=1, horizontal=True,
                               key="alert_periode", label_visibility="collapsed")
            jours = PERIODES[periode]
            df_plot = serie if jours is None else serie[serie["date"] > serie["date"].max() - pd.Timedelta(days=jours)]
            fig, n_hors, n_total = _alert_chart(df_plot, var, var_label, limit, mode, demo_point)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f"Barres rouges : jours hors seuil ({n_hors} sur {n_total} jours affiches). "
                       f"Courbe orange : moyenne mobile sur 7 jours.")

    # ---------- Declenchement
    depassement = status == "critique"
    alert_key = f"{site_label}|{var}|{current_date:%Y-%m-%d}|{limit:.2f}|{'demo' if demo_on else 'reel'}"
    last30 = serie[serie["date"] > serie["date"].max() - pd.Timedelta(days=30)][var]
    stats = {
        "moyenne_7j": float(serie[var].iloc[-7:].mean()),
        "moyenne_30j": float(last30.mean()),
        "jours_depassement_30j": int((last30 > limit).sum() if mode == "max" else (last30 < limit).sum()),
    }

    def _send(test, send_mode):
        recs = []
        if with_ai:
            breach = {"site": site_label, "variable": var_label, "unite": unit, "type_seuil": mode,
                      "valeur_du_jour": round(current_value, 2), "seuil": round(limit, 2),
                      "ecart_au_seuil_pct": round((ratio - 1) * 100, 1),
                      "moyenne_historique": round(float(hist_mean), 2), **{k: round(v, 2) for k, v in stats.items()}}
            recs, _moteur = ai_agent.breach_recommendations(alert_key, breach)
        subject, body, body_html = alerts.build_alert_message(
            site_label, var_label, current_value, limit, unit, status, mode=mode,
            value_date=date_str, stats=stats, recommendations=recs, test=test)
        ok, msg = alerts.send_email_alert(recipients, subject, body, body_html)
        alerts.log_alert(alert_key if not test else alert_key + "|test", site_label, var_label,
                         current_value, limit, status, recipients, send_mode, ok)
        return ok, msg, subject, body

    with st.container(border=True):
        st.markdown("##### Envoi des alertes")
        if depassement and auto_send and recipients and not invalid:
            if alerts.already_sent(alert_key):
                st.info("Ce depassement a deja fait l'objet d'un email : il ne sera pas renvoye.")
            else:
                with st.spinner("Depassement detecte : envoi de l'alerte..."):
                    ok, msg, subject, body = _send(test=False, send_mode="automatique")
                (st.success if ok else st.error)(("Alerte envoyee automatiquement. " if ok else "") + msg)
                with st.expander("Apercu du message envoye"):
                    st.text(f"Objet : {subject}\n\n{body}")
        elif depassement and not recipients:
            st.warning("Depassement detecte, mais aucune adresse destinataire n'est renseignee.")
        elif not depassement:
            st.write("Aucun depassement sur la derniere valeur : aucune alerte a envoyer.")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Envoyer l'alerte maintenant", use_container_width=True, key="alert_send_now",
                         disabled=not recipients or bool(invalid)):
                ok, msg, subject, body = _send(test=not depassement, send_mode="manuel")
                (st.success if ok else st.error)(msg)
                with st.expander("Apercu du message envoye", expanded=True):
                    st.text(f"Objet : {subject}\n\n{body}")
        with b2:
            st.caption("Sans depassement, le bouton envoie un email marque [TEST], utile pour verifier la "
                       "configuration.")

    # ---------- Journal des envois
    with st.container(border=True):
        st.markdown("##### Historique des emails envoyes")
        log = alerts.read_log()
        if log.empty:
            st.caption("Aucun email envoye pour l'instant.")
        else:
            st.dataframe(log.drop(columns=["cle"]).iloc[::-1], use_container_width=True, hide_index=True, height=240)
