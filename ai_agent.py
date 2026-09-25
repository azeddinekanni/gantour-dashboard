"""
Agent IA (Google Gemini) : interprete les signaux calcules par signals.py et
redige une synthese et des recommandations actionnables.

Principes :
- L'agent ne recoit que des indicateurs agreges (aucune donnee brute de l'OCP),
  car les requetes de l'offre gratuite peuvent etre utilisees par Google.
- Il lui est interdit d'inventer des chiffres : il ne cite que ceux du contexte.
- La reponse est regeneree uniquement quand l'empreinte des signaux change
  (cache Streamlit indexe sur l'empreinte), ce qui economise le quota gratuit.
- Sans cle API ou en cas d'erreur, un moteur de regles prend le relais :
  le dashboard ne tombe jamais en panne.
"""
import json
import os

import streamlit as st

DEFAULT_MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """Tu es un analyste senior en controle de gestion miniere pour le site OCP de Gantour \
(mines de Benguerir, Bouchane et Mzinda ; unites de traitement de Youssoufia : calcination UC, sechage US, laverie UL).

Tu recois un JSON contenant des indicateurs de marche et des indicateurs internes DEJA CALCULES.

Regles strictes :
1. N'utilise QUE les chiffres presents dans le JSON. N'invente aucun chiffre, aucune probabilite, aucune source.
2. Une "frequence_hist_hausse_mois_suivant_pct" est une frequence historique, pas une prevision : presente-la comme telle.
3. Si une information manque ou vaut null, ne la mentionne pas ou signale qu'elle est indisponible.
4. Chaque recommandation doit citer au moins un indicateur du JSON dans "indicateurs_lies" (utilise les libelles).
5. Les recommandations doivent etre concretes et actionnables par un responsable de site : achats, energie,
   planification de la production, maintenance, stocks, contrats, suivi de consommation specifique.
6. Tiens compte du role : pour un indicateur "cout", une hausse est defavorable ; pour "valorisation", une baisse est defavorable.
7. Reste prudent et factuel : il s'agit d'aide a la decision.
8. Reponds en francais, sans accents si possible, de facon concise.

Reponds UNIQUEMENT avec un JSON valide de cette forme :
{
  "synthese": "2 a 3 phrases sur la situation globale",
  "risque_principal": "une phrase",
  "recommandations": [
    {"priorite": "haute|moyenne|basse", "titre": "...", "action": "...", "justification": "...", "indicateurs_lies": ["..."]}
  ],
  "points_de_vigilance": ["..."]
}
Maximum 5 recommandations, triees de la plus prioritaire a la moins prioritaire."""

CHAT_PROMPT = """Tu es l'assistant d'analyse des couts du site OCP Gantour. Tu reponds a la question de l'utilisateur \
en t'appuyant UNIQUEMENT sur le JSON de contexte fourni (indicateurs de marche et internes deja calcules). \
N'invente aucun chiffre. Si la reponse n'est pas dans le contexte, dis-le clairement et indique quelle donnee manquerait. \
Reponds en francais, en 5 phrases maximum."""

ACTIONS_COUT = {
    "brent": "Verifier les conditions des contrats d'approvisionnement en carburant et suivre la consommation "
             "specifique (L/t) des engins et des unites thermiques.",
    "diesel": "Optimiser les cycles des engins (temps d'attente, charge utile, trajets) et suivre la consommation "
              "de gasoil par tonne extraite.",
    "gaz_ue": "Examiner la consommation thermique des unites de calcination et de sechage et lisser le planning "
              "pour eviter les pointes.",
    "uree": "Anticiper une hausse du cout des explosifs : revoir le plan de tir (maille, charge specifique) "
            "et le calendrier des commandes.",
    "acide_sulf": "Impact surtout en aval (transformation) : informer les equipes Safi / Jorf Lasfar ; "
                  "effet indirect sur Gantour.",
}


def _get_secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


def agent_available():
    return bool(_get_secret("GEMINI_API_KEY"))


def _call_gemini(system_prompt, user_content, json_mode):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_get_secret("GEMINI_API_KEY"))
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.2,
        response_mime_type="application/json" if json_mode else "text/plain",
    )
    resp = client.models.generate_content(
        model=_get_secret("GEMINI_MODEL", DEFAULT_MODEL),
        contents=user_content,
        config=config,
    )
    return resp.text


def _clean_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    return json.loads(text[: text.rfind("}") + 1])


# ---------------------------------------------------------------- Repli par regles
def rule_based_insights(context):
    recs = []
    for s in context["indicateurs_marche"]:
        if not s["defavorable"] or s["niveau"] == "stable":
            continue
        prio = "haute" if s["niveau"] == "tension" else "moyenne"
        if s["role"] == "cout":
            action = ACTIONS_COUT.get(s["cle"], "Suivre l'impact de cet intrant sur les couts et ajuster le budget.")
        else:
            action = "Anticiper une pression sur les marges : prioriser la reduction du cout unitaire sur les sites les plus couteux."
        recs.append({
            "priorite": prio,
            "titre": f"{s['libelle']} en {s['direction']} ({(s['variation_mensuelle_pct'] or 0):+.1f} % sur un mois)",
            "action": action,
            "justification": f"Ecart a la moyenne 12 mois : {s['zscore_12m']:+.2f} ecart-type ; niveau {s['niveau']}.",
            "indicateurs_lies": [s["libelle"]],
        })
    for i in context["indicateurs_internes"]:
        v = i["variation_cout_unitaire_pct"]
        if v is not None and v >= 5:
            recs.append({
                "priorite": "haute" if v >= 10 else "moyenne",
                "titre": f"Cout unitaire en hausse sur {i['perimetre']} ({v:+.1f} %)",
                "action": "Analyser les determinants significatifs dans l'onglet Analyse econometrique et "
                          "verifier les consommations specifiques des 30 derniers jours.",
                "justification": f"Cout unitaire moyen 30 j : {i['cout_unitaire_30j_dh_t']} DH/t.",
                "indicateurs_lies": [i["perimetre"]],
            })
    ordre = {"haute": 0, "moyenne": 1, "basse": 2}
    recs = sorted(recs, key=lambda r: ordre[r["priorite"]])[:5]

    n_def = sum(1 for s in context["indicateurs_marche"] if s["defavorable"] and s["niveau"] != "stable")
    health = context["score_sante"]
    synthese = (f"Score de sante : {health['score']}/100 ({health['niveau']}). "
                f"{n_def} indicateur(s) de marche evoluent defavorablement.")
    if not recs:
        recs = [{"priorite": "basse", "titre": "Situation stable",
                 "action": "Maintenir le suivi mensuel des indicateurs.",
                 "justification": "Aucun signal defavorable significatif.", "indicateurs_lies": []}]
    return {"synthese": synthese, "risque_principal": recs[0]["titre"],
            "recommandations": recs, "points_de_vigilance": health["penalites"]}


# ---------------------------------------------------------------- Points d'entree
@st.cache_data(ttl=24 * 3600, show_spinner=False)
def generate_insights(fingerprint, _context):
    """
    Le cache est indexe sur `fingerprint` uniquement (le parametre `_context`
    commence par un underscore, Streamlit ne le hache pas). L'agent n'est donc
    rappele que lorsque la situation change reellement.
    """
    if not agent_available():
        return {**rule_based_insights(_context), "moteur": "regles", "erreur": None}
    try:
        text = _call_gemini(SYSTEM_PROMPT, json.dumps(_context, ensure_ascii=False), json_mode=True)
        data = _clean_json(text)
        data.setdefault("recommandations", [])
        data.setdefault("points_de_vigilance", [])
        return {**data, "moteur": "gemini", "erreur": None}
    except Exception as err:
        return {**rule_based_insights(_context), "moteur": "regles", "erreur": str(err)[:200]}


def ask_agent(question, context):
    if not agent_available():
        return "Agent IA non configure : ajoutez GEMINI_API_KEY dans les secrets Streamlit."
    try:
        payload = f"CONTEXTE :\n{json.dumps(context, ensure_ascii=False)}\n\nQUESTION :\n{question}"
        return _call_gemini(CHAT_PROMPT, payload, json_mode=False)
    except Exception as err:
        return f"Erreur de l'agent IA : {str(err)[:200]}"
