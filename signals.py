"""
Moteur de signaux : TOUS les chiffres affiches et transmis a l'agent IA sont
calcules ici, de facon deterministe et documentee. L'agent IA ne produit aucun
chiffre : il redige uniquement l'interpretation et les recommandations.

Methodologie (a reprendre dans le memoire) :
- Variation mensuelle (MoM) et annuelle (YoY) en %.
- Z-score : ecart de la derniere valeur a la moyenne des 12 mois precedents,
  en nombre d'ecarts-types.
- Niveau : "tension" si |z| >= 2 ou |MoM| >= 10 % ; "surveillance" si |z| >= 1
  ou |MoM| >= 5 % ; sinon "stable".
- Frequence historique de hausse : sur les 10 dernieres annees, part des mois
  ou le prix a monte le mois suivant, parmi les mois presentant la meme tendance
  sur 3 mois que la situation actuelle. C'est une frequence empirique, pas une
  prevision ; elle n'est affichee que si au moins 12 cas comparables existent.
- Score de sante (0-100) : 100 moins des penalites explicites (voir health_score).
"""
import hashlib
import json
from datetime import date

import numpy as np
import pandas as pd

from market_data import INDICATORS, series_for

Z_SURVEILLANCE, Z_TENSION = 1.0, 2.0
MOM_SURVEILLANCE, MOM_TENSION = 5.0, 10.0
MIN_CAS_COMPARABLES = 12

PENALITES_MARCHE = {"tension": 12, "surveillance": 6, "stable": 0}
SEUIL_INTERNE_FORT, SEUIL_INTERNE_MODERE = 10.0, 5.0
PENALITES_INTERNES = {"forte": 12, "moderee": 6}


def _pct(a, b):
    return float((a / b - 1) * 100) if b not in (0, None) and pd.notna(b) else None


def _r(x, n=2):
    return None if x is None or pd.isna(x) else round(float(x), n)


# ---------------------------------------------------------------- Marche
def indicator_signal(key, series):
    meta = INDICATORS[key]
    s = series.dropna().sort_index()
    if len(s) < 14:
        return None

    last, prev = s.iloc[-1], s.iloc[-2]
    mom = _pct(last, prev)
    yoy = _pct(last, s.iloc[-13])
    tendance_3m = _pct(last, s.iloc[-4])

    window = s.iloc[-13:-1]
    std = window.std()
    z = float((last - window.mean()) / std) if std and std > 0 else 0.0

    # Frequence empirique de hausse le mois suivant, a tendance 3 mois comparable
    hist = pd.DataFrame({"tend": s.pct_change(3), "suiv": s.pct_change().shift(-1)}).dropna().iloc[-120:]
    signe = np.sign(tendance_3m or 0)
    comparables = hist[np.sign(hist["tend"]) == signe]
    if len(comparables) >= MIN_CAS_COMPARABLES:
        freq_hausse = float((comparables["suiv"] > 0).mean() * 100)
    else:
        freq_hausse = None

    if abs(z) >= Z_TENSION or abs(mom or 0) >= MOM_TENSION:
        niveau = "tension"
    elif abs(z) >= Z_SURVEILLANCE or abs(mom or 0) >= MOM_SURVEILLANCE:
        niveau = "surveillance"
    else:
        niveau = "stable"

    if (mom or 0) > 0.5:
        direction = "hausse"
    elif (mom or 0) < -0.5:
        direction = "baisse"
    else:
        direction = "stable"

    defavorable = (meta["role"] == "cout" and direction == "hausse") or \
                  (meta["role"] == "valorisation" and direction == "baisse")

    return {
        "cle": key,
        "libelle": meta["label"],
        "unite": meta["unit"],
        "source": meta["source"],
        "role": meta["role"],
        "date_derniere_valeur": s.index[-1].strftime("%Y-%m"),
        "derniere_valeur": _r(last),
        "variation_mensuelle_pct": _r(mom, 1),
        "variation_annuelle_pct": _r(yoy, 1),
        "tendance_3m_pct": _r(tendance_3m, 1),
        "zscore_12m": _r(z, 2),
        "frequence_hist_hausse_mois_suivant_pct": _r(freq_hausse, 0),
        "nb_cas_comparables": int(len(comparables)),
        "niveau": niveau,
        "direction": direction,
        "defavorable": bool(defavorable),
    }


def compute_indicator_signals(market_df):
    out = []
    for key in INDICATORS:
        s = series_for(market_df, key)
        sig = indicator_signal(key, s) if not s.empty else None
        if sig:
            out.append(sig)
    return out


# ---------------------------------------------------------------- Interne (Gantour)
def _window_compare(df, cost_col, prod_col, days=30):
    latest = df["date"].max()
    last = df[df["date"] > latest - pd.Timedelta(days=days)]
    prev = df[(df["date"] <= latest - pd.Timedelta(days=days)) &
              (df["date"] > latest - pd.Timedelta(days=2 * days))]
    cu_last, cu_prev = last[cost_col].mean(), prev[cost_col].mean()
    pr_last, pr_prev = last[prod_col].sum(), prev[prod_col].sum()
    return {
        "cout_unitaire_30j_dh_t": _r(cu_last),
        "variation_cout_unitaire_pct": _r(_pct(cu_last, cu_prev), 1),
        "production_30j_t": _r(pr_last, 0),
        "variation_production_pct": _r(_pct(pr_last, pr_prev), 1),
        "date_derniere_donnee": latest.strftime("%Y-%m-%d"),
    }


def internal_signals(mines_df, phase_dfs, phase_labels):
    out = []
    for code, g in mines_df.groupby("mines"):
        label = g["mine_label"].iloc[0] if "mine_label" in g else str(code)
        out.append({"perimetre": label, "type": "mine",
                    **_window_compare(g, "cout_unitaire_mines", "production_mines")})
    for code, dfp in phase_dfs.items():
        out.append({"perimetre": phase_labels.get(code, code), "type": "phase de traitement",
                    **_window_compare(dfp, "cout_unitaire", "production")})
    return out


# ---------------------------------------------------------------- Score de sante
def health_score(ind_signals, internal):
    score, penalites = 100, []
    for s in ind_signals:
        if s["defavorable"] and s["niveau"] != "stable":
            p = PENALITES_MARCHE[s["niveau"]]
            score -= p
            penalites.append(f"{s['libelle']} : {s['direction']} ({s['niveau']}) -{p}")
    for i in internal:
        v = i["variation_cout_unitaire_pct"]
        if v is None:
            continue
        if v >= SEUIL_INTERNE_FORT:
            p = PENALITES_INTERNES["forte"]
        elif v >= SEUIL_INTERNE_MODERE:
            p = PENALITES_INTERNES["moderee"]
        else:
            continue
        score -= p
        penalites.append(f"{i['perimetre']} : cout unitaire +{v:.1f} % sur 30 j -{p}")
    score = max(0, min(100, score))
    niveau = "Bon" if score >= 75 else ("Sous surveillance" if score >= 50 else "Critique")
    return {"score": int(score), "niveau": niveau, "penalites": penalites}


# ---------------------------------------------------------------- Contexte et empreinte
def build_context(ind_signals, internal, health):
    return {
        "date_analyse": date.today().isoformat(),
        "perimetre": "Site OCP Gantour : mines Benguerir, Bouchane, Mzinda ; "
                     "unites de traitement de Youssoufia (UC calcination, US sechage, UL laverie)",
        "indicateurs_marche": ind_signals,
        "indicateurs_internes": internal,
        "score_sante": health,
    }


def _bucket(v):
    if v is None:
        return "na"
    if v >= SEUIL_INTERNE_FORT:
        return "hausse_forte"
    if v >= SEUIL_INTERNE_MODERE:
        return "hausse"
    if v <= -SEUIL_INTERNE_MODERE:
        return "baisse"
    return "stable"


def fingerprint(ind_signals, internal):
    """
    Empreinte qualitative de la situation. Elle ne change que si un niveau,
    une direction, une date de publication ou une categorie de variation
    interne change : de petites fluctuations ne relancent pas l'agent IA.
    """
    payload = {
        "marche": sorted((s["cle"], s["niveau"], s["direction"], s["date_derniere_valeur"]) for s in ind_signals),
        "interne": sorted((i["perimetre"], _bucket(i["variation_cout_unitaire_pct"])) for i in internal),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]
