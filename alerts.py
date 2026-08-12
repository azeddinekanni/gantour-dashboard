import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def evaluate_threshold(current_value, limit_value, mode="max"):
    if limit_value is None or limit_value == 0:
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
    "inconnu": "#6B7280"
}

STATUS_LABELS = {
    "normal": "Normal",
    "vigilance": "Vigilance",
    "alerte": "Alerte",
    "critique": "Depassement critique",
    "inconnu": "Seuil non defini"
}


def build_alert_message(site_label, variable_label, current_value, limit_value, unit, status):
    date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    subject = f"[ALERTE OCP GANTOUR] {STATUS_LABELS.get(status, status)} - {site_label} - {variable_label}"
    body = (
        f"Bonjour,\n\n"
        f"Le systeme de suivi des couts operationnels du site Gantour signale un depassement de seuil.\n\n"
        f"Site / Phase concerne(e) : {site_label}\n"
        f"Variable surveillee : {variable_label}\n"
        f"Valeur constatee : {current_value:,.2f} {unit}\n"
        f"Limite fixee : {limit_value:,.2f} {unit}\n"
        f"Statut : {STATUS_LABELS.get(status, status)}\n"
        f"Date de detection : {date_str}\n\n"
        f"Merci de bien vouloir analyser la situation et engager les actions correctives necessaires.\n\n"
        f"Message genere automatiquement par le tableau de bord OCP Gantour Intelligence."
    )
    return subject, body


def send_email_alert(recipients, subject, body):
    sender = os.getenv("ALERT_EMAIL_SENDER")
    password = os.getenv("ALERT_EMAIL_PASSWORD")
    smtp_server = os.getenv("ALERT_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("ALERT_SMTP_PORT", "587"))

    if not sender or not password:
        return False, "Configuration email absente. Renseignez ALERT_EMAIL_SENDER et ALERT_EMAIL_PASSWORD dans le fichier .env pour activer l'envoi reel. Message pret mais non envoye (mode simulation)."

    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipients, message.as_string())
        server.quit()
        return True, "Alerte envoyee avec succes aux managers concernes."
    except Exception as error:
        return False, f"Echec de l'envoi : {error}"