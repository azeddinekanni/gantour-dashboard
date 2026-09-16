import streamlit as st
import hashlib
import base64
import time
import random
from pathlib import Path

try:
    import streamlit.components.v1 as components
except Exception:
    components = None

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
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stSidebarNav"] {display: none;}
            .block-container { padding-top: 1.2rem !important; }

            [data-testid="stAppViewContainer"] {
                background: #0B1310 !important;
            }

            @keyframes gtGridShift { from { background-position: 0 0, 0 0; } to { background-position: 34px 34px, 34px 34px; } }
            @keyframes gtParticleFloat { 0%, 100% { transform: translateY(0) translateX(0); } 50% { transform: translateY(-14px) translateX(6px); } }
            @keyframes gtHaloPulse { 0%, 100% { opacity: 0.28; transform: scale(1); } 50% { opacity: 0.46; transform: scale(1.06); } }
            @keyframes gtScanMove { 0% { top: -10%; opacity: 0; } 10% { opacity: 0.5; } 90% { opacity: 0.5; } 100% { top: 110%; opacity: 0; } }
            @keyframes gtRadarBreathe { 0% { transform: scale(0.85); opacity: 0.35; } 70% { opacity: 0; } 100% { transform: scale(1.15); opacity: 0; } }
            @keyframes gtMiniRadarSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
            @keyframes gtFadeInUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            @keyframes gtConnectorLight { 0% { top: 0%; opacity: 0; } 15% { opacity: 1; } 85% { opacity: 1; } 100% { top: 100%; opacity: 0; } }
            @keyframes gtTermLine { from { opacity: 0; transform: translateX(-4px); } to { opacity: 0.9; transform: translateX(0); } }
            @keyframes gtBarFill { from { width: 0%; } to { width: 100%; } }
            @keyframes gtErrorPop { from { transform: scale(0.97); opacity: 0; } to { transform: scale(1); opacity: 1; } }
            @keyframes gtDotPulse { 0%,100% { opacity:1; transform:scale(1); } 50% { opacity:0.4; transform:scale(0.8); } }
            @keyframes gtAccessPop { from { opacity:0; transform:scale(0.9); } to { opacity:1; transform:scale(1); } }
            @keyframes gtLineFade { from { opacity:0; transform:translateY(4px); } to { opacity:0.9; transform:translateY(0); } }
            @keyframes gtAccessFadeOut { from { opacity:1; } to { opacity:0; visibility:hidden; } }

            .gt-seq-1 { animation: gtFadeInUp 0.5s ease-out 0.2s both; }
            .gt-seq-2 { animation: gtFadeInUp 0.5s ease-out 0.35s both; }
            .gt-seq-3 { animation: gtFadeInUp 0.5s ease-out 0.5s both; }

            .gt-login-card div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(18,28,24,0.55) !important;
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(0,230,118,0.20) !important;
                border-radius: 18px !important;
                box-shadow: 0 0 22px rgba(0,230,118,0.06);
            }

            div[data-testid="stTextInput"] input {
                background: #0D1520 !important;
                border: 1px solid rgba(0,230,118,0.25) !important;
                color: #E8EDEB !important;
                border-radius: 8px !important;
                padding: 6px 12px !important;
                font-size: 13px !important;
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
            }
            div[data-testid="stTextInput"] input:focus {
                border-color: #00FF8C !important;
                box-shadow: 0 0 0 2px rgba(0,255,140,0.35), 0 0 14px rgba(0,255,140,0.35) !important;
            }
            div[data-testid="stTextInput"] input::placeholder { color: #5A6B65 !important; }

            div[data-testid="stFormSubmitButton"] button {
                background: linear-gradient(135deg, #00c26f, #00e88a) !important;
                color: #06110B !important;
                font-weight: 800 !important;
                border: none !important;
                border-radius: 10px !important;
                box-shadow: 0 0 16px rgba(0,232,138,0.35);
                transition: transform 0.25s ease, box-shadow 0.25s ease;
            }
            div[data-testid="stFormSubmitButton"] button:hover {
                transform: translateX(3px) scale(1.02);
                box-shadow: 0 0 22px rgba(0,232,138,0.55) !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_background():
    random.seed(7)
    particles_html = "".join(
        f'<div style="position:absolute; left:{random.randint(4,96)}%; top:{random.randint(4,96)}%; '
        f'width:{random.choice([2,3,3,4])}px; height:{random.choice([2,3,3,4])}px; border-radius:50%; '
        f'background:#00FF8C; opacity:{random.uniform(0.10,0.28):.2f}; '
        f'box-shadow:0 0 6px rgba(0,255,140,0.6); '
        f'animation: gtParticleFloat {random.uniform(13,22):.1f}s ease-in-out {random.uniform(0,8):.1f}s infinite;"></div>'
        for _ in range(34)
    )

    logo_b64 = _get_logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = (
            f'<img src="data:image/png;base64,{logo_b64}" style="'
            f'position:relative; width:100vmin; height:100vmin; object-fit:contain; '
            f'opacity:0.06; transform:translate(6vw, -3vh); z-index:1;" />'
        )

    st.markdown(
        f"""
        <div style="position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;
            display:flex;align-items:center;justify-content:center;">
            <div style="position:absolute;inset:0;
                background-image: linear-gradient(rgba(0,230,118,0.05) 1px, transparent 1px),
                                   linear-gradient(90deg, rgba(0,230,118,0.05) 1px, transparent 1px);
                background-size: 34px 34px, 34px 34px;
                animation: gtGridShift 16s linear infinite;"></div>
            <div style="position:absolute; width:70vmin; height:70vmin; border-radius:50%;
                background:radial-gradient(circle, rgba(0,230,118,0.14) 0%, transparent 70%);
                filter: blur(20px); transform:translateX(6vw);
                animation: gtHaloPulse 5s ease-in-out infinite;"></div>
            <div style="position:absolute; top:0; bottom:0; left:0; width:1px;
                background:linear-gradient(180deg, transparent, rgba(0,230,118,0.30) 15%, rgba(0,230,118,0.30) 85%, transparent);"></div>
            <div style="position:absolute; top:0; bottom:0; right:0; width:1px;
                background:linear-gradient(180deg, transparent, rgba(0,230,118,0.18) 15%, rgba(0,230,118,0.18) 85%, transparent);"></div>
            <div style="position:absolute; left:0; right:0; height:2px;
                background:linear-gradient(90deg, transparent, rgba(0,230,118,0.5), transparent);
                animation: gtScanMove 26s linear infinite;"></div>
            <div style="position:absolute; width:38vmin; height:38vmin; border-radius:50%;
                border:1px solid rgba(0,230,118,0.45); transform:translateX(6vw);
                animation: gtRadarBreathe 4.5s ease-out infinite;"></div>
            {particles_html}
            {logo_html}
        </div>
        <div style="position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;">
            <div style="position:absolute; top:26px; left:26px; width:34px; height:34px; border-radius:50%;
                border:1px solid rgba(0,230,118,0.25); overflow:hidden;">
                <div style="position:absolute; top:50%; left:50%; width:50%; height:1px;
                    background:linear-gradient(90deg, rgba(0,230,118,0.8), transparent);
                    transform-origin:left center;
                    animation: gtMiniRadarSpin 3s linear infinite;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_clock():
    if components is None:
        return
    components.html(
        """
        <div style="text-align:right;font-family:'Inter',sans-serif;padding-top:6px;">
            <div style="display:flex;align-items:center;justify-content:flex-end;gap:6px;margin-bottom:4px;">
                <span style="font-size:9.5px;color:#00E676;font-weight:800;letter-spacing:1px;">SYSTEM ONLINE</span>
                <span style="width:6px;height:6px;border-radius:50%;background:#00FF8C;
                    box-shadow:0 0 6px rgba(0,255,140,0.8);animation:gtDotPulse 1.6s ease-in-out infinite;"></span>
            </div>
            <div style="font-size:10px;color:#00E676;font-weight:700;letter-spacing:1.5px;">CASABLANCA</div>
            <div id="gt-clock-time" style="font-size:19px;color:#E8EDEB;font-weight:800;
                font-family:'IBM Plex Mono',monospace;">--:--:--</div>
            <div id="gt-clock-date" style="font-size:10.5px;color:#8DA69C;">-</div>
        </div>
        <script>
        function gtUpdateClock() {
            const now = new Date();
            const t = new Intl.DateTimeFormat('fr-FR', {timeZone:'Africa/Casablanca',
                hour:'2-digit', minute:'2-digit', second:'2-digit'}).format(now);
            const d = new Intl.DateTimeFormat('fr-FR', {timeZone:'Africa/Casablanca',
                day:'numeric', month:'long', year:'numeric'}).format(now);
            document.getElementById('gt-clock-time').textContent = t;
            document.getElementById('gt-clock-date').textContent = d;
        }
        gtUpdateClock();
        setInterval(gtUpdateClock, 1000);
        </script>
        """,
        height=90,
    )


def check_authentication():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    login_placeholder = st.empty()

    with login_placeholder.container():
        _inject_login_css()
        _render_background()

        col_clock_l, col_clock_r = st.columns([2.4, 1])
        with col_clock_r:
            _render_clock()

        st.write("")
        col1, col2, col3 = st.columns([1, 1.7, 0.9])

        with col1:
            st.markdown(
                '<div style="max-width:100%; overflow-wrap:break-word; word-break:break-word; '
                'font-size:38px;font-weight:800;color:#00FF8C;opacity:0.05;line-height:1.15;'
                'letter-spacing:0.5px;user-select:none;margin-top:70px;">'
                'GANTOUR<br>INTELLIGENCE</div>',
                unsafe_allow_html=True,
            )
            st.write("")
            steps = [("AUTHENTIFICATION", True), ("CHARGEMENT DES DONNÉES", False),
                     ("ANALYSE DES COÛTS", False), ("TABLEAU DE BORD", False)]
            steps_html = ""
            for i, (label, active) in enumerate(steps):
                if active:
                    dot_html = ('<span style="width:8px;height:8px;border-radius:50%;background:#00FF8C;'
                                'box-shadow:0 0 8px rgba(0,255,140,0.7);flex-shrink:0;"></span>')
                    c = "#00FF8C"
                else:
                    dot_html = ('<span style="width:8px;height:8px;border-radius:50%;background:transparent;'
                                'border:1.5px solid #3D4A45;flex-shrink:0;"></span>')
                    c = "#5A6B65"
                steps_html += (
                    f'<div style="display:flex;align-items:center;gap:10px;">'
                    f'{dot_html}<span style="font-size:10.5px;font-weight:700;letter-spacing:0.8px;color:{c};">{label}</span>'
                    f'</div>'
                )
                if i < len(steps) - 1:
                    steps_html += (
                        '<div style="position:relative;width:1px;height:20px;'
                        'background:rgba(255,255,255,0.12);margin-left:4px;overflow:hidden;">'
                        '<div style="position:absolute;left:0;width:1px;height:6px;'
                        'background:#00FF8C;box-shadow:0 0 6px rgba(0,255,140,0.8);'
                        f'animation: gtConnectorLight 2.4s ease-in-out {i * 0.5:.1f}s infinite;"></div>'
                        '</div>'
                    )
            st.markdown(f'<div>{steps_html}</div>', unsafe_allow_html=True)

        with col2:
            logo_b64 = _get_logo_base64()
            badge_html = (
                f'<div style="display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:24px;">'
                + (f'<img src="data:image/png;base64,{logo_b64}" style="width:40px;height:40px;object-fit:contain;" />' if logo_b64 else "")
                + '<div style="text-align:left;background:rgba(0,230,118,0.08);border:1px solid rgba(0,230,118,0.25);'
                'border-radius:8px;padding:4px 10px;">'
                '<div style="font-size:9px;color:#00E676;font-weight:800;letter-spacing:0.5px;">ANALYTICS ENGINE</div>'
                '<div style="font-size:8px;color:#8DA69C;">OLS · Random Forest</div>'
                '<div style="font-size:8px;color:#00FF8C;font-weight:700;">● ONLINE</div>'
                '</div></div>'
            )
            st.markdown(
                f'<div class="gt-seq-1" style="text-align:center;margin-bottom:4px;">'
                f'{badge_html}'
                '<div style="font-size:28px;font-weight:800;color:#E8EDEB;letter-spacing:-0.4px;'
                'text-shadow:0 0 16px rgba(0,230,118,0.25);">OCP Gantour Intelligence</div>'
                '<div style="font-size:12.5px;color:#8DA69C;font-weight:600;margin-top:12px;">'
                'Analyse econometrique des couts operationnels - Site Gantour</div>'
                '</div>'
                '<div class="gt-seq-2" style="text-align:center;margin-bottom:30px;">'
                '<div style="font-size:16px;color:#00C97A;font-weight:800;letter-spacing:1.5px;'
                'text-shadow:0 0 10px rgba(0,201,122,0.4);">Predict. Assess. Decide.</div>'
                '</div>',
                unsafe_allow_html=True,
            )

            st.markdown('<div class="gt-seq-3 gt-login-card">', unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(
                    '<div style="font-size:14px;font-weight:800;color:#00E676;'
                    'padding-bottom:10px;margin-bottom:16px;border-bottom:1px solid rgba(0,230,118,0.15);">'
                    'Connexion</div>',
                    unsafe_allow_html=True,
                )
                with st.form("login_form", border=False):
                    _icon_user = (
                        '<svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                        '<defs><radialGradient id="gUser" cx="35%" cy="28%" r="75%">'
                        '<stop offset="0%" stop-color="#8CFFC0"/><stop offset="55%" stop-color="#00C97A"/>'
                        '<stop offset="100%" stop-color="#00693A"/></radialGradient></defs>'
                        '<circle cx="12" cy="12" r="11" fill="url(#gUser)" stroke="#0A2F1D" stroke-width="0.6"/>'
                        '<circle cx="12" cy="9.3" r="3.1" fill="#FFFFFF"/>'
                        '<path d="M5.3 19c0-3.6 3-6.2 6.7-6.2s6.7 2.6 6.7 6.2" fill="#FFFFFF"/></svg>'
                    )
                    _icon_lock = (
                        '<svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                        '<defs><radialGradient id="gLock" cx="35%" cy="28%" r="75%">'
                        '<stop offset="0%" stop-color="#8CFFC0"/><stop offset="55%" stop-color="#00C97A"/>'
                        '<stop offset="100%" stop-color="#00693A"/></radialGradient></defs>'
                        '<circle cx="12" cy="12" r="11" fill="url(#gLock)" stroke="#0A2F1D" stroke-width="0.6"/>'
                        '<rect x="7.8" y="11" width="8.4" height="6.6" rx="1.3" fill="#FFFFFF"/>'
                        '<path d="M9.2 11V8.9a2.8 2.8 0 0 1 5.6 0V11" fill="none" stroke="#FFFFFF" '
                        'stroke-width="1.5" stroke-linecap="round"/></svg>'
                    )
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">'
                        f'{_icon_user}<span style="font-size:13px;font-weight:700;color:#00E676;">Utilisateur</span></div>',
                        unsafe_allow_html=True,
                    )
                    username = st.text_input("Utilisateur", placeholder="ex. admin",
                                              label_visibility="collapsed").strip()
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:8px;margin:10px 0 2px;">'
                        f'{_icon_lock}<span style="font-size:13px;font-weight:700;color:#00E676;">Mot de passe</span></div>',
                        unsafe_allow_html=True,
                    )
                    password = st.text_input("Mot de passe", type="password", placeholder="••••••••",
                                              label_visibility="collapsed")
                    st.write("")
                    submitted = st.form_submit_button("Accéder à la plateforme →", use_container_width=True)

                    if submitted:
                        user = USERS.get(username)
                        if user and user["password_hash"] == _hash(password):
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            st.session_state.role = user["role"]
                            st.session_state.full_name = user["full_name"]
                            login_placeholder.empty()
                            st.rerun()
                        else:
                            st.markdown(
                                '<div style="background:rgba(255,92,92,0.12);border:1px solid rgba(255,92,92,0.4);'
                                'border-radius:10px;padding:12px 16px;margin-top:8px;animation: gtErrorPop 0.35s ease-out;">'
                                '<div style="font-size:13px;font-weight:800;color:#FF5C5C;">Accès refusé</div>'
                                '<div style="font-size:12px;color:#E8EDEB;margin-top:2px;">'
                                'Identifiant ou mot de passe incorrect.</div></div>',
                                unsafe_allow_html=True,
                            )
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(
                '<div style="text-align:center;margin-top:22px;font-size:11px;color:#8DA69C;letter-spacing:0.3px;">'
                'Version 1.0 &middot; Connexion sécurisée &middot; &copy; OCP Gantour Intelligence</div>',
                unsafe_allow_html=True,
            )

        _term_ts = time.strftime("%H:%M:%S")
        _term_checks = ["Connexion sécurisée établie", "Base de données mines chargée",
                         "Modèles économétriques prêts", "Tableau de bord initialisé"]
        _term_lines_html = "".join(
            f'<div style="opacity:0;animation: gtTermLine 0.4s ease-out {0.3 + i * 0.25:.2f}s forwards;">'
            f'<span style="color:#00FF8C;">✔</span> {c}</div>'
            for i, c in enumerate(_term_checks)
        )
        st.markdown(
            f"""
            <div style="position:fixed;bottom:18px;left:26px;z-index:1;
                font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:#8DA69C;
                background:rgba(7,11,18,0.5);border:1px solid rgba(0,230,118,0.12);
                border-radius:8px;padding:10px 14px;max-width:260px;pointer-events:none;">
                <div style="color:#5A6B65;margin-bottom:4px;">[{_term_ts}]</div>
                <div style="color:#E8EDEB;margin-bottom:6px;">&gt; Connexion...</div>
                {_term_lines_html}
                <div style="margin-top:10px;color:#00E676;font-weight:700;font-size:9.5px;letter-spacing:0.5px;">
                    AUTHENTIFICATION</div>
                <div style="width:100px;height:5px;background:#1B2530;border-radius:4px;overflow:hidden;margin-top:3px;">
                    <div style="height:100%;background:#00FF8C;border-radius:4px;
                        animation: gtBarFill 3.5s ease-out 1s forwards;width:0%;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return False


def logout_button():
    if st.sidebar.button("Se deconnecter", use_container_width=True):
        for key in ["authenticated", "username", "role", "full_name"]:
            st.session_state.pop(key, None)
        st.rerun()