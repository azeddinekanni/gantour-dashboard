"""
Systeme d'alertes OCP Gantour : evaluation des seuils, construction et envoi
des emails (texte + HTML), journal des alertes envoyees (anti-doublon).

Configuration (dans .streamlit/secrets.toml en local, et dans Settings > Secrets
sur Streamlit Cloud) :
    ALERT_EMAIL_SENDER   = "adresse.expediteur@gmail.com"
    ALERT_EMAIL_PASSWORD = "mot de passe d'application Gmail (16 caracteres)"
    ALERT_SMTP_SERVER    = "smtp.gmail.com"   # optionnel
    ALERT_SMTP_PORT      = "587"              # optionnel
"""
import html
import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import pandas as pd

try:
    import streamlit as st
except Exception:  # permet d'utiliser le module hors Streamlit (script automatique)
    st = None

LOG_PATH = Path(__file__).resolve().parent / "data" / "alerts_log.csv"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")


def _get_secret(name, default=None):
    if st is not None:
        try:
            if name in st.secrets:
                return str(st.secrets[name])
        except Exception:
            pass
    return os.getenv(name, default)


# ---------------------------------------------------------------- Seuils
def evaluate_threshold(current_value, limit_value, mode="max"):
    if limit_value is None or limit_value == 0 or pd.isna(current_value):
        return "inconnu", 0
    ratio = current_value / limit_value
    if mode == "max":
        if ratio >= 1.0:
            return "critique", ratio
        elif ratio >= 0.9:
            return "alerte", ratio
        elif ratio >= 0.75:
            return "vigilance", ratio
        return "normal", ratio
    else:
        if ratio <= 1.0:
            return "critique", ratio
        elif ratio <= 1.1:
            return "alerte", ratio
        elif ratio <= 1.25:
            return "vigilance", ratio
        return "normal", ratio


STATUS_COLORS = {
    "normal": "#009A44",
    "vigilance": "#F5A623",
    "alerte": "#F5A623",
    "critique": "#D92D20",
    "inconnu": "#6B7280",
}

STATUS_LABELS = {
    "normal": "Normal",
    "vigilance": "Vigilance",
    "alerte": "Alerte (proche du seuil)",
    "critique": "Depassement du seuil",
    "inconnu": "Seuil non defini",
}


# ---------------------------------------------------------------- Configuration email
def email_config_ok():
    return bool(_get_secret("ALERT_EMAIL_SENDER") and _get_secret("ALERT_EMAIL_PASSWORD"))


def parse_recipients(raw):
    """Retourne (adresses valides, adresses invalides)."""
    items = [r.strip() for r in re.split(r"[,;\s]+", raw or "") if r.strip()]
    valid = [r for r in items if EMAIL_RE.match(r)]
    invalid = [r for r in items if not EMAIL_RE.match(r)]
    return valid, invalid


# ---------------------------------------------------------------- Message
def build_alert_message(site_label, variable_label, current_value, limit_value, unit, status,
                        mode="max", value_date=None, stats=None, recommendations=None, test=False):
    """Retourne (sujet, corps texte, corps HTML)."""
    stats = stats or {}
    recommendations = recommendations or []
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    value_date = value_date or now
    ecart = (current_value / limit_value - 1) * 100 if limit_value else 0
    sens = "Limite maximale" if mode == "max" else "Objectif minimum"
    prefix = "[TEST] " if test else ""
    subject = f"{prefix}[ALERTE OCP GANTOUR] {STATUS_LABELS.get(status, status)} - {site_label} - {variable_label}"

    lignes = [
        ("Site / phase", site_label),
        ("Variable surveillee", variable_label),
        ("Valeur constatee", f"{current_value:,.2f} {unit} (le {value_date})"),
        (sens, f"{limit_value:,.2f} {unit}"),
        ("Ecart au seuil", f"{ecart:+.1f} %"),
        ("Statut", STATUS_LABELS.get(status, status)),
    ]
    if stats.get("moyenne_7j") is not None:
        lignes.append(("Moyenne 7 derniers jours", f"{stats['moyenne_7j']:,.2f} {unit}"))
    if stats.get("moyenne_30j") is not None:
        lignes.append(("Moyenne 30 derniers jours", f"{stats['moyenne_30j']:,.2f} {unit}"))
    if stats.get("jours_depassement_30j") is not None:
        lignes.append(("Jours hors seuil (30 derniers jours)", str(stats["jours_depassement_30j"])))

    intro = ("Ceci est un email de TEST envoye depuis le tableau de bord." if test else
             "Le systeme de suivi des couts operationnels du site Gantour signale un depassement de seuil.")

    # Texte brut
    body = f"Bonjour,\n\n{intro}\n\n"
    body += "\n".join(f"{k} : {v}" for k, v in lignes)
    if recommendations:
        body += "\n\nRecommandations :\n" + "\n".join(f"- {r}" for r in recommendations)
    body += (f"\n\nDate de detection : {now}\n\n"
             "Message genere automatiquement par le tableau de bord OCP Gantour Intelligence.")

    # HTML
    color = STATUS_COLORS.get(status, "#6B7280")
    rows = "".join(
        f'<tr><td style="padding:6px 12px;color:#555;">{html.escape(k)}</td>'
        f'<td style="padding:6px 12px;font-weight:600;">{html.escape(v)}</td></tr>'
        for k, v in lignes
    )
    recs_html = ""
    if recommendations:
        recs_html = ('<h3 style="font-size:15px;margin:22px 0 8px;">Recommandations</h3><ul style="padding-left:18px;">'
                     + "".join(f'<li style="margin-bottom:6px;">{html.escape(r)}</li>' for r in recommendations)
                     + "</ul>")
    body_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:620px;color:#1E2227;">
      <div style="background:{color};color:#fff;padding:14px 18px;border-radius:8px 8px 0 0;">
        <div style="font-size:12px;opacity:0.9;">{'TEST - ' if test else ''}OCP GANTOUR INTELLIGENCE</div>
        <div style="font-size:18px;font-weight:700;margin-top:4px;">{html.escape(STATUS_LABELS.get(status, status))}</div>
      </div>
      <div style="border:1px solid #ddd;border-top:none;padding:18px;border-radius:0 0 8px 8px;">
        <p>Bonjour,</p><p>{html.escape(intro)}</p>
        <table style="border-collapse:collapse;width:100%;font-size:14px;">{rows}</table>
        {recs_html}
        <p style="font-size:12px;color:#777;margin-top:22px;">Detection : {now}<br>
        Message genere automatiquement par le tableau de bord OCP Gantour Intelligence.</p>
      </div>
    </div>"""
    return subject, body, body_html


# ---------------------------------------------------------------- Envoi
def send_email_alert(recipients, subject, body, body_html=None):
    sender = _get_secret("ALERT_EMAIL_SENDER")
    password = _get_secret("ALERT_EMAIL_PASSWORD")
    smtp_server = _get_secret("ALERT_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(_get_secret("ALERT_SMTP_PORT", "587"))

    if not sender or not password:
        return False, ("Envoi impossible : l'adresse expediteur n'est pas configuree. Ajoutez "
                       "ALERT_EMAIL_SENDER et ALERT_EMAIL_PASSWORD dans les secrets.")
    if not recipients:
        return False, "Aucune adresse destinataire valide."

    message = MIMEMultipart("alternative")
    message["From"] = f"OCP Gantour Intelligence <{sender}>"
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain", "utf-8"))
    if body_html:
        message.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=20)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=20)
            server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipients, message.as_string())
        server.quit()
        return True, f"Email envoye a : {', '.join(recipients)}"
    except smtplib.SMTPAuthenticationError:
        return False, ("Echec d'authentification Gmail : utilisez un mot de passe d'application "
                       "(et non le mot de passe habituel du compte).")
    except Exception as error:
        return False, f"Echec de l'envoi : {error}"


# ---------------------------------------------------------------- Journal
LOG_COLUMNS = ["horodatage", "cle", "site", "variable", "valeur", "seuil", "statut",
               "destinataires", "mode_envoi", "resultat"]


def read_log():
    try:
        return pd.read_csv(LOG_PATH)
    except Exception:
        return pd.DataFrame(columns=LOG_COLUMNS)


def already_sent(key):
    log = read_log()
    if log.empty:
        return False
    return bool(((log["cle"] == key) & (log["resultat"] == "envoye")).any())


def log_alert(key, site, variable, value, limit, status, recipients, send_mode, success):
    row = pd.DataFrame([{
        "horodatage": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cle": key, "site": site, "variable": variable,
        "valeur": round(float(value), 2), "seuil": round(float(limit), 2),
        "statut": status, "destinataires": ", ".join(recipients),
        "mode_envoi": send_mode, "resultat": "envoye" if success else "echec",
    }])
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        row.to_csv(LOG_PATH, mode="a", header=not LOG_PATH.exists(), index=False)
    except Exception:
        pass
