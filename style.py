import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root{
  --ocp-bg: #0B1310;
  --ocp-panel: #121C18;
  --ocp-panel-2: #17221D;
  --ocp-green: #00E676;
  --ocp-green-2: #00C97A;
  --ocp-green-dark: #00A85E;
  --ocp-orange: #FFB020;
  --ocp-red: #FF5C5C;
  --ocp-blue: #3B82F6;
  --ocp-ink: #EAF7F0;
  --ocp-muted: #8DA69C;
  --ocp-line: rgba(0,230,118,0.16);
  --ocp-line-hover: rgba(0,230,118,0.40);
  --radius: 16px;
  --shadow-glow: 0 0 22px rgba(0,230,118,0.06);
  --shadow-glow-hover: 0 0 28px rgba(0,230,118,0.14);
}

@keyframes ocpFadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes ocpPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.65; } }

.stApp{
  background: var(--ocp-bg);
  font-family: 'Inter', sans-serif;
  color: var(--ocp-ink);
}

[data-testid="stAppViewContainer"]{ background: var(--ocp-bg) !important; }
.main .block-container{ background: transparent; padding-top: 1.5rem; }

h1, h2, h3, h4{
  font-family: 'Inter', sans-serif;
  font-weight: 700 !important;
  letter-spacing: -0.3px;
  color: var(--ocp-ink) !important;
}
p, span, label, div{ color: var(--ocp-ink); }
.stCaption, [data-testid="stCaptionContainer"]{ color: var(--ocp-muted) !important; }

section[data-testid="stSidebar"]{ background: #0A100D; border-right: 1px solid var(--ocp-line); }
section[data-testid="stSidebar"] *{ color: #C9D6CF !important; }

/* ── Ecran de connexion ── */
.login-wrapper{ display:flex; justify-content:center; margin-top: 40px; margin-bottom: 10px; }
.login-card{
  background: linear-gradient(135deg, rgba(0,168,94,0.14) 0%, rgba(18,28,24,0.96) 65%), var(--ocp-panel);
  border: 1px solid var(--ocp-line);
  border-radius: var(--radius);
  padding: 34px 40px;
  text-align:center;
  box-shadow: var(--shadow-glow);
  width: 100%;
  animation: ocpFadeIn 400ms ease-out both;
}
.login-title{ font-size: 26px; font-weight:800; color: var(--ocp-green); letter-spacing:-0.4px; text-shadow: 0 0 14px rgba(0,230,118,0.35); }
.login-subtitle{ font-size: 13.5px; color: var(--ocp-muted); margin-top:6px; }

/* ── Hero header ── */
.ocp-hero{
  position: relative;
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 22px;
  padding: 26px 32px;
  border: 1px solid var(--ocp-line);
  background:
    linear-gradient(115deg, rgba(0,168,94,0.16) 0%, rgba(11,19,16,0.92) 65%),
    repeating-linear-gradient(135deg, rgba(0,230,118,0.03) 0 2px, transparent 2px 28px),
    var(--ocp-panel);
  box-shadow: var(--shadow-glow);
  animation: ocpFadeIn 400ms ease-out both;
}
.ocp-hero-eyebrow{ color: var(--ocp-green); font-size:12.5px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; text-shadow: 0 0 10px rgba(0,230,118,0.4); }
.ocp-hero-title{ font-size: 26px; font-weight: 800; color: #F3FFF8; letter-spacing: -0.4px; margin-top:6px; }
.ocp-hero-sub{ color: var(--ocp-muted); font-size:13.5px; margin-top:6px; max-width:760px; }

/* ── KPI cards ── */
.kpi-card{
  background: var(--ocp-panel);
  border-radius: var(--radius);
  padding: 18px 20px;
  border: 1px solid var(--ocp-line);
  box-shadow: var(--shadow-glow);
  height: 100%;
  transition: transform 250ms ease, border-color 250ms ease, box-shadow 250ms ease;
  animation: ocpFadeIn 400ms ease-out both;
}
.kpi-card:hover{ transform: translateY(-3px); border-color: var(--ocp-line-hover); box-shadow: var(--shadow-glow-hover); }
.kpi-label{ font-size:12px; font-weight:600; color:var(--ocp-muted); text-transform:uppercase; letter-spacing:0.4px; }
.kpi-value{ font-size:26px; font-weight:800; color: var(--ocp-ink); margin-top:4px; font-family:'IBM Plex Mono', monospace; }
.kpi-delta-up{ color: var(--ocp-red); font-size:12.5px; font-weight:700; text-shadow: 0 0 8px rgba(255,92,92,0.35); }
.kpi-delta-down{ color: var(--ocp-green); font-size:12.5px; font-weight:700; text-shadow: 0 0 8px rgba(0,230,118,0.35); }

/* ── Cartes de section ── */
.section-card{
  background: var(--ocp-panel);
  border-radius: var(--radius);
  padding: 20px 22px;
  border: 1px solid var(--ocp-line);
  box-shadow: var(--shadow-glow);
  margin-bottom: 18px;
  transition: border-color 250ms ease, box-shadow 250ms ease;
  animation: ocpFadeIn 400ms ease-out both;
}
.section-card:hover{ border-color: var(--ocp-line-hover); box-shadow: var(--shadow-glow-hover); }

/* ── Badges de statut ── */
.badge{ display:inline-block; padding: 4px 13px; border-radius:20px; font-size:12px; font-weight:700; border:1px solid transparent; }
.badge-normal{ background: rgba(0,230,118,0.12); color: var(--ocp-green); border-color: rgba(0,230,118,0.35); text-shadow: 0 0 8px rgba(0,230,118,0.4); }
.badge-vigilance{ background: rgba(255,176,32,0.12); color: var(--ocp-orange); border-color: rgba(255,176,32,0.35); text-shadow: 0 0 8px rgba(255,176,32,0.4); }
.badge-alerte{ background: rgba(255,176,32,0.12); color: var(--ocp-orange); border-color: rgba(255,176,32,0.35); text-shadow: 0 0 8px rgba(255,176,32,0.4); }
.badge-critique{ background: rgba(255,92,92,0.12); color: var(--ocp-red); border-color: rgba(255,92,92,0.35); text-shadow: 0 0 8px rgba(255,92,92,0.4); }
.badge-inconnu{ background: rgba(141,166,156,0.12); color: var(--ocp-muted); border-color: rgba(141,166,156,0.3); }

/* ── Bandeaux d'alerte ── */
.alert-banner{
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 14px;
  font-size: 14px;
  font-weight:600;
  border-left: 5px solid;
  background: var(--ocp-panel-2);
}
.alert-critique{ border-color: var(--ocp-red); color: #FFC9C9; box-shadow: 0 0 18px rgba(255,92,92,0.10); }
.alert-vigilance{ border-color: var(--ocp-orange); color: #FFE1A8; box-shadow: 0 0 18px rgba(255,176,32,0.10); }
.alert-normal{ border-color: var(--ocp-green); color: #C6FBE0; box-shadow: 0 0 18px rgba(0,230,118,0.10); }

/* ── Journal de nettoyage des données ── */
.data-issue{
  background: rgba(255,176,32,0.08);
  border-left: 5px solid var(--ocp-orange);
  border-radius:10px;
  padding: 12px 16px;
  font-size: 13px;
  color:#FFE1A8;
  margin-bottom:10px;
}

/* ── Tableaux ── */
[data-testid="stDataFrame"], [data-testid="stDataEditor"]{
  background: var(--ocp-panel) !important;
  border-radius: var(--radius);
  border: 1px solid var(--ocp-line);
}
[data-testid="stDataFrame"] *, [data-testid="stDataEditor"] *{ color: var(--ocp-ink) !important; }

/* ── Metriques natives st.metric ── */
[data-testid="stMetric"]{
  background: var(--ocp-panel);
  border: 1px solid var(--ocp-line);
  border-radius: var(--radius);
  padding: 14px 18px;
}
[data-testid="stMetricLabel"]{ color: var(--ocp-muted) !important; }
[data-testid="stMetricValue"]{ color: var(--ocp-ink) !important; font-family:'IBM Plex Mono', monospace; }
[data-testid="stMetricDelta"]{ color: var(--ocp-green) !important; }

/* ── Selectbox / multiselect / radio ── */
div[data-baseweb="select"] > div{
  background: var(--ocp-panel-2) !important;
  border-color: var(--ocp-line) !important;
  color: var(--ocp-ink) !important;
}
div[data-baseweb="popover"] ul{ background: var(--ocp-panel-2) !important; }
div[data-baseweb="popover"] li{ color: var(--ocp-ink) !important; }
div[data-baseweb="popover"] li:hover{ background: rgba(0,230,118,0.10) !important; }
.stRadio label, .stCheckbox label{ color: var(--ocp-ink) !important; }
.stRadio [role="radiogroup"] label div:first-child{ border-color: var(--ocp-green) !important; }

/* ── Onglets ── */
button[data-baseweb="tab"]{ font-weight: 600; font-size: 13px; transition: color .3s ease, text-shadow .3s ease; }
button[data-baseweb="tab"][aria-selected="true"], button[data-baseweb="tab"][aria-selected="true"] *{
  color: var(--ocp-green) !important;
  font-weight: 700 !important;
  text-shadow: 0 0 10px rgba(0,230,118,0.35) !important;
  -webkit-text-fill-color: var(--ocp-green) !important;
}
button[data-baseweb="tab"][aria-selected="false"], button[data-baseweb="tab"][aria-selected="false"] *{
  color: var(--ocp-muted) !important;
  -webkit-text-fill-color: var(--ocp-muted) !important;
}
[data-baseweb="tab-highlight"]{ background-color: var(--ocp-green) !important; box-shadow: 0 0 8px rgba(0,230,118,0.6); }
[data-baseweb="tab-border"]{ background-color: var(--ocp-line) !important; }

/* ── Expanders ── */
[data-testid="stExpander"]{ background: var(--ocp-panel); border: 1px solid var(--ocp-line); border-radius: var(--radius); }

/* ── Boutons ── */
.stButton button{
  background: var(--ocp-panel-2) !important;
  color: var(--ocp-ink) !important;
  border: 1px solid var(--ocp-line) !important;
  border-radius: 10px !important;
  transition: border-color 200ms ease, box-shadow 200ms ease;
}
.stButton button:hover{ border-color: var(--ocp-green) !important; box-shadow: 0 0 12px rgba(0,230,118,0.25); }
.stButton button:active{ transform: scale(0.98); }

/* ── Sliders / number input / text input ── */
[data-testid="stSlider"] label{ color: var(--ocp-ink) !important; }
div[data-baseweb="slider"] div[role="slider"]{ background: var(--ocp-green) !important; box-shadow: 0 0 8px rgba(0,230,118,0.6); }
input, textarea{ background: var(--ocp-panel-2) !important; color: var(--ocp-ink) !important; border-color: var(--ocp-line) !important; }

/* ── Alertes natives st.success/st.warning/st.info ── */
[data-testid="stNotificationContentSuccess"]{ background: rgba(0,230,118,0.10) !important; }
[data-testid="stNotificationContentWarning"]{ background: rgba(255,176,32,0.10) !important; }
[data-testid="stNotificationContentInfo"]{ background: rgba(59,130,246,0.10) !important; }

/* ── Barre d'outils Plotly discrète ── */
.js-plotly-plot .plotly .modebar{ opacity: 0; transition: opacity 200ms ease; }
.js-plotly-plot:hover .plotly .modebar{ opacity: 1; }

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(eyebrow, title, subtitle):
    st.markdown(
        f"""
        <div class="ocp-hero">
            <div class="ocp-hero-eyebrow">{eyebrow}</div>
            <div class="ocp-hero-title">{title}</div>
            <div class="ocp-hero-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def kpi_card(label, value, delta=None, delta_positive_is_bad=True):
    delta_html = ""
    if delta is not None:
        is_up = delta >= 0
        arrow = "\u25b2" if is_up else "\u25bc"
        cls = "kpi-delta-up" if (is_up == delta_positive_is_bad) else "kpi-delta-down"
        delta_html = f'<div class="{cls}">{arrow} {abs(delta):.1f}%</div>'
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True
    )


def badge(status_key, status_label):
    st.markdown(f'<span class="badge badge-{status_key}">{status_label}</span>', unsafe_allow_html=True)


def style_plotly(fig):
    fig.update_layout(
        paper_bgcolor="#121C18",
        plot_bgcolor="#121C18",
        font_color="#EAF7F0",
        legend=dict(font=dict(color="#EAF7F0")),
        xaxis=dict(gridcolor="rgba(0,230,118,0.10)", linecolor="rgba(0,230,118,0.25)", zerolinecolor="rgba(0,230,118,0.10)"),
        yaxis=dict(gridcolor="rgba(0,230,118,0.10)", linecolor="rgba(0,230,118,0.25)", zerolinecolor="rgba(0,230,118,0.10)"),
    )
    return fig