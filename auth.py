import streamlit as st
import hashlib
import base64
from pathlib import Path

USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "Administrateur",
        "full_name": "Administrateur Gantour"
    }
}

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo_ocp.png"


def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


def _get_logo_base64():
    if LOGO_PATH.exists():
        return base64.b64encode(LOGO_PATH.read_bytes()).decode()
    return None


def _inject_login_css():
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 20% 20%, rgba(0,150,80,0.12) 0%, transparent 45%),
                radial-gradient(circle at 80% 70%, rgba(0,150,80,0.10) 0%, transparent 45%),
                linear-gradient(180deg, #061410 0%, #050d0b 100%);
        }
        [data-testid="stHeader"] { background: transparent; }

        .login-badge-row {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 14px;
            margin-top: 30px;
        }
        .login-logo-box {
            background: #0c1f19;
            border: 1px solid rgba(0,200,120,0.35);
            border-radius: 12px;
            padding: 8px 14px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-logo-box img { height: 34px; }
        .login-status-box {
            background: #0c1f19;
            border: 1px solid rgba(0,200,120,0.35);
            border-radius: 10px;
            padding: 6px 14px;
            font-size: 11px;
            color: #7fe3b4;
            text-align: left;
            line-height: 1.3;
        }
        .login-status-box .dot {
            color: #17e08a;
            font-size: 9px;
        }

        .login-title {
            text-align: center;
            font-size: 40px;
            font-weight: 800;
            color: #f1fbf6;
            margin-top: 22px;
            letter-spacing: 0.5px;
        }
        .login-subtitle {
            text-align: center;
            color: #9fb9ad;
            font-size: 15px;
            margin-top: 6px;
        }
        .login-tagline {
            text-align: center;
            color: #17e08a;
            font-weight: 700;
            letter-spacing: 2px;
            margin-top: 4px;
            margin-bottom: 30px;
        }

        .login-steps {
            margin-top: 40px;
            padding-left: 10px;
            border-left: 2px solid rgba(255,255,255,0.08);
        }
        .login-step {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-left: -7px;
            margin-bottom: 26px;
            font-size: 13px;
            letter-spacing: 1px;
            color: #6f8a80;
        }
        .login-step.active { color: #eafff4; font-weight: 700; }
        .login-step .bullet {
            width: 10px; height: 10px; border-radius: 50%;
            background: #1a352c; border: 2px solid #2a4a3d;
        }
        .login-step.active .bullet {
            background: #17e08a; border-color: #17e08a;
            box-shadow: 0 0 10px #17e08a;
        }

        .login-terminal {
            margin-top: 30px;
            background: #08130f;
            border: 1px solid rgba(0,200,120,0.25);
            border-radius: 10px;
            padding: 14px 16px;
            font-family: monospace;
            font-size: 12px;
            color: #8fe6bb;
        }
        .login-terminal .line-ok::before { content: "✓ "; color: #17e08a; }
        .login-terminal .ts { color: #4d7566; margin-bottom: 6px; }
        .login-terminal .bar-label {
            color: #17e08a; font-weight: 700; margin-top: 10px; font-size: 11px;
        }
        .login-terminal .bar {
            height: 4px; background: #123024; border-radius: 3px; margin-top: 6px; overflow: hidden;
        }
        .login-terminal .bar-fill {
            height: 100%; width: 100%; background: #17e08a;
        }

        .login-card {
            background: rgba(10, 26, 21, 0.75);
            border: 1px solid rgba(0,200,120,0.25);
            border-radius: 16px;
            padding: 34px 34px 26px 34px;
            margin-top: 30px;
        }
        .login-card-heading {
            color: #eafff4;
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 18px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 12px;
        }
        .login-field-label {
            color: #cfeee0;
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 4px;
        }

        div[data-testid="stForm"] input {
            background: #08150f !important;
            border: 1px solid rgba(0,200,120,0.3) !important;
            color: #eafff4 !important;
            border-radius: 8px !important;
        }
        div[data-testid="stForm"] button {
            background: linear-gradient(90deg, #12c47a, #0ea86a) !important;
            color: #04160f !important;
            font-weight: 700 !important;
            border: none !important;
            border-radius: 10px !important;
            box-shadow: 0 0 18px rgba(20,220,140,0.35);
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def check_authentication():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    _inject_login_css()
    logo_b64 = _get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}">' if logo_b64 else "OCP"

    st.markdown(
        f"""
        <div class="login-badge-row">
            <div class="login-logo-box">{logo_html}</div>
            <div class="login-status-box">
                <span class="dot">●</span> Gantour Intelligence<br>
                <span class="dot">●</span> ONLINE
            </div>
        </div>
        <div class="login-title">OCP Gantour Intelligence</div>
        <div class="login-subtitle">Analyse econometrique des couts operationnels - Site Gantour</div>
        <div class="login-tagline">PREDICT · ASSESS · DECIDE</div>
        """,
        unsafe_allow_html=True
    )

    left, right = st.columns([1, 1.3])

    with left:
        st.markdown(
            """
            <div class="login-steps">
                <div class="login-step active"><div class="bullet"></div>AUTHENTIFICATION</div>
                <div class="login-step"><div class="bullet"></div>CHARGEMENT DES DONNEES</div>
                <div class="login-step"><div class="bullet"></div>ANALYSE DES COUTS</div>
                <div class="login-step"><div class="bullet"></div>TABLEAU DE BORD</div>
            </div>
            <div class="login-terminal">
                <div class="ts">&gt; Connexion...</div>
                <div class="line-ok">API OK</div>
                <div class="line-ok">Base de donnees OK</div>
                <div class="line-ok">Moteur d'analyse charge</div>
                <div class="line-ok">Modeles prets</div>
                <div class="bar-label">AUTHENTIFICATION</div>
                <div class="bar"><div class="bar-fill"></div></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with right:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="login-card-heading">Connexion</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown('<div class="login-field-label">Utilisateur</div>', unsafe_allow_html=True)
            username = st.text_input("Utilisateur", label_visibility="collapsed", placeholder="ex. admin")

            st.markdown('<div class="login-field-label">Mot de passe</div>', unsafe_allow_html=True)
            password = st.text_input("Mot de passe", type="password", label_visibility="collapsed")

            submitted = st.form_submit_button("Acceder a la plateforme →", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

        if submitted:
            user = USERS.get(username)
            if user and user["password_hash"] == _hash(password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.role = user["role"]
                st.session_state.full_name = user["full_name"]
                st.rerun()
            else:
                st.error("Identifiant ou mot de passe incorrect.")

    return False


def logout_button():
    if st.sidebar.button("Se deconnecter", use_container_width=True):
        for key in ["authenticated", "username", "role", "full_name"]:
            st.session_state.pop(key, None)
        st.rerun()