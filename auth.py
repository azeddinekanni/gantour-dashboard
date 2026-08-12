import streamlit as st
import hashlib

USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "Administrateur",
        "full_name": "Administrateur Gantour"
    }
}


def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_authentication():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown(
        """
        <div class="login-wrapper">
            <div class="login-card">
                <div class="login-title">OCP Gantour Intelligence</div>
                <div class="login-subtitle">Analyse econometrique des couts operationnels - Site Gantour</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        with st.form("login_form"):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)

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