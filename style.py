import functools

@functools.lru_cache(maxsize=1)
def _load_morocco_svg_b64(path):
    import base64
    from pathlib import Path
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")
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
  --ocp-grid-line: rgba(0,230,118,0.05);
}

@keyframes ocpFadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes ocpPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.65; } }

.stApp{
  background:
    linear-gradient(var(--ocp-grid-line) 1px, transparent 1px) 0 0 / 36px 36px,
    linear-gradient(90deg, var(--ocp-grid-line) 1px, transparent 1px) 0 0 / 36px 36px,
    var(--ocp-bg);
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

[data-testid="stVerticalBlockBorderWrapper"]{
  background: var(--ocp-panel);
  border-radius: var(--radius);
  border: 1px solid var(--ocp-line);
  box-shadow: var(--shadow-glow);
}

/* ── Badges de statut ── */
.badge{ display:inline-block; padding: 4px 13px; border-radius:20px; font-size:12px; font-weight:700; border:1px solid transparent; }
.badge-normal{ background: rgba(0,230,118,0.12); color: var(--ocp-green); border-color: rgba(0,230,118,0.35); text-shadow: 0 0 8px rgba(0,230,118,0.4); }
.badge-vigilance{ background: rgba(255,176,32,0.12); color: var(--ocp-orange); border-color: rgba(255,176,32,0.35); text-shadow: 0 0 8px rgba(255,176,32,0.4); }
.badge-alerte{ background: rgba(255,176,32,0.12); color: var(--ocp-orange); border-color: rgba(255,176,32,0.35); text-shadow: 0 0 8px rgba(255,176,32,0.4); }
.badge-critique{ background: rgba(255,92,92,0.12); color: var(--ocp-red); border-color: rgba(255,92,92,0.35); text-shadow: 0 0 8px rgba(255,92,92,0.4); }
.badge-inconnu{ background: rgba(141,166,156,0.12); color: var(--ocp-muted); border-color: rgba(141,166,156,0.3); }
.badge-dot{ display:inline-block; width:7px; height:7px; border-radius:50%; background:currentColor; margin-right:6px; vertical-align:middle; box-shadow:0 0 6px currentColor; }

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
div[data-baseweb="popover"],
div[data-baseweb="menu"],
div[data-baseweb="layer"]{
  background-color: var(--ocp-panel-2) !important;
}
div[data-baseweb="popover"] *,
div[data-baseweb="menu"] *,
div[data-baseweb="layer"] *{
  color: var(--ocp-ink) !important;
}
ul[role="listbox"], div[role="listbox"]{
  background-color: var(--ocp-panel-2) !important;
}
li[role="option"], div[role="option"]{
  background-color: var(--ocp-panel-2) !important;
  color: var(--ocp-ink) !important;
}
li[role="option"]:hover, div[role="option"]:hover{
  background-color: rgba(0,230,118,0.14) !important;
}
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
[data-testid="stHeader"]{
  background: var(--ocp-bg) !important;
}
[data-testid="stToolbar"]{
  background: transparent !important;
}
[data-testid="stDecoration"]{
  background: transparent !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stSpinner"] { color: var(--ocp-green) !important; }
[data-testid="stSpinner"] svg { color: var(--ocp-green) !important; }
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
    st.markdown(
        f'<span class="badge badge-{status_key}"><span class="badge-dot"></span>{status_label}</span>',
        unsafe_allow_html=True
    )


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
def national_value_chain_map(sites, phases=None, height=460):
    """
    Carte schematique legere (aucune dependance a un fichier externe) de la chaine
    de valeur du phosphate. Contour du pays simplifie (silhouette approximative,
    calibree sur les memes coordonnees que les sites) pour garantir un affichage
    instantane. Sans JavaScript.
    sites = [{"name": str, "production": float, "cost": float}, ...] (mines Gantour)
    phases = [{"name": "UC"/"US"/"UL", "production": float, "cost": float}, ...]
    """
    import html as _html
    import streamlit.components.v1 as components

    phases = phases or []
    phases_by_code = {p["name"]: p for p in phases}

    NODES = {
        "khouribga":   (612.8, 210.0, "mine", "Khouribga"),
        "benguerir":   (566.0, 250.0, "mine", "Benguerir"),
        "bouchane":    (543.0, 233.0, "mine", "Bouchane"),
        "mzinda":      (513.0, 250.0, "mine", "Mzinda"),
        "youssoufia":  (541.0, 276.0, "usine_ville", "Youssoufia"),
        "jorf_lasfar": (522.0, 180.1, "transform_port", "Jorf Lasfar"),
        "safi":        (490.5, 232.3, "transform_port", "Safi"),
        "casablanca":  (576.9, 157.2, "port", "Casablanca"),
    }

    # Sous-unites de traitement du phosphate a Youssoufia
    PHASE_NODES = {
        "UC": (533.0, 291.0, "Calcination (UC)"),
        "US": (541.0, 296.0, "Sechage (US)"),
        "UL": (549.0, 291.0, "Laverie (UL)"),
    }

    country_path = (
        "M669,22 L730,55 L800,85 L870,120 L855,190 L800,240 "
        "L743,295 L680,330 L610,340 L556,287 L500,320 L471,356 "
        "L455,300 L490,232 L470,190 L522,180 L577,157 L616,133 Z"
    )

    gantour_keys = {"benguerir", "mzinda", "bouchane"}
    live_data = {s["name"].split(" ")[0].split("-")[0].strip().lower(): s for s in sites}

    def _find_live(label):
        low = label.lower()
        for k, v in live_data.items():
            if k in low or low in k:
                return v
        return None

    nodes_svg = ""
    lines_svg = ""

    kx, ky = NODES["khouribga"][0], NODES["khouribga"][1]
    jx, jy = NODES["jorf_lasfar"][0], NODES["jorf_lasfar"][1]
    lines_svg += f'<line x1="{kx}" y1="{ky}" x2="{jx}" y2="{jy}" stroke="#00E676" stroke-width="2.2" marker-end="url(#arrowGreen)" />'

    yx, yy = NODES["youssoufia"][0], NODES["youssoufia"][1]
    for mine_key in ["benguerir", "mzinda", "bouchane"]:
        mx, my = NODES[mine_key][0], NODES[mine_key][1]
        lines_svg += (
            f'<line x1="{mx}" y1="{my}" x2="{yx}" y2="{yy}" stroke="#00E676" '
            f'stroke-width="1.8" marker-end="url(#arrowGreen)" />'
        )

    sx, sy = NODES["safi"][0], NODES["safi"][1]
    jx2, jy2 = NODES["jorf_lasfar"][0], NODES["jorf_lasfar"][1]
    cx, cy = NODES["casablanca"][0], NODES["casablanca"][1]
    for (x2, y2) in [(sx, sy), (jx2, jy2), (cx, cy)]:
        lines_svg += (
            f'<line x1="{yx}" y1="{yy}" x2="{x2}" y2="{y2}" stroke="#FFB020" '
            f'stroke-width="1.6" stroke-dasharray="5,4" marker-end="url(#arrowOrange)" />'
        )

    export_ports = [("jorf_lasfar", -55, -18), ("jorf_lasfar", -50, 10),
                     ("safi", -55, -12),
                     ("casablanca", -50, -20)]
    for key, dx, dy in export_ports:
        px, py = NODES[key][0], NODES[key][1]
        lines_svg += (
            f'<line x1="{px}" y1="{py}" x2="{px + dx}" y2="{py + dy}" stroke="#3B82F6" '
            f'stroke-width="1.4" stroke-dasharray="4,3" marker-end="url(#arrowBlue)" opacity="0.85" />'
        )

    icon_map = {"mine": "\u26cf", "transform_port": "\U0001F3ED", "port": "\u2693", "usine_ville": "\U0001F3ED"}
    color_map = {"mine": "#00E676", "transform_port": "#FFB020", "port": "#3B82F6", "usine_ville": "#FFB020"}

    for key, (x, y, ntype, label) in NODES.items():
        color = color_map[ntype]
        icon = icon_map[ntype]
        live = _find_live(label) if key in gantour_keys else None
        if live:
            prod = f'{live["production"]:,.0f} t'.replace(",", " ")
            cost = f'{live["cost"]:,.2f} DH/t'
            tip_text = f'{prod} &#183; {cost}'
        elif ntype == "mine":
            tip_text = "Hors perimetre de l'etude"
        elif ntype == "usine_ville":
            tip_text = "3 unites : UC, US, UL (survolez ci-dessous)"
        else:
            tip_text = {"transform_port": "Transformation / Port", "port": "Port"}[ntype]

        pulse = f'<circle cx="{x}" cy="{y}" r="13" fill="{color}" opacity="0.18" class="mine-pulse" />' if live else ""
        nodes_svg += (
            f'<g class="mine-node">'
            f'{pulse}'
            f'<circle cx="{x}" cy="{y}" r="6" fill="#0B1310" stroke="{color}" stroke-width="1.6" />'
            f'<text x="{x}" y="{y + 2.3}" text-anchor="middle" font-size="6.5" fill="#EAF7F0">{icon}</text>'
            f'<text class="mine-label" x="{x}" y="{y - 11}" text-anchor="middle" font-family="Inter, sans-serif" '
            f'font-size="8" font-weight="800" fill="#EAF7F0" style="text-shadow:0 0 4px #000, 0 0 4px #000;">{_html.escape(label)}</text>'
            f'<g class="mine-tip" transform="translate({x},{y})">'
            f'<rect x="-58" y="-46" width="116" height="18" rx="6" fill="rgba(11,19,16,0.97)" '
            f'stroke="rgba(0,230,118,0.45)" stroke-width="0.8" />'
            f'<text x="0" y="-34" text-anchor="middle" font-family="Inter, sans-serif" '
            f'font-size="6.5" fill="#00E676">{tip_text}</text>'
            f'</g></g>'
        )

    for code, (x, y, full_label) in PHASE_NODES.items():
        p = phases_by_code.get(code)
        if p:
            prod = f'{p["production"]:,.0f} t'.replace(",", " ")
            cost = f'{p["cost"]:,.2f} DH/t'
            tip_text = f'{prod} &#183; {cost}'
        else:
            tip_text = "Donnees indisponibles"
        nodes_svg += (
            f'<g class="mine-node">'
            f'<circle cx="{x}" cy="{y}" r="4" fill="#0B1310" stroke="#FFB020" stroke-width="1.3" />'
            f'<text class="mine-label" x="{x}" y="{y - 7}" text-anchor="middle" font-family="Inter, sans-serif" '
            f'font-size="6" font-weight="800" fill="#EAF7F0" style="text-shadow:0 0 4px #000, 0 0 4px #000;">{code}</text>'
            f'<g class="mine-tip" transform="translate({x},{y})">'
            f'<rect x="-54" y="-46" width="108" height="26" rx="5" fill="rgba(11,19,16,0.97)" '
            f'stroke="rgba(255,176,32,0.5)" stroke-width="0.8" />'
            f'<text x="0" y="-35" text-anchor="middle" font-family="Inter, sans-serif" '
            f'font-size="6" font-weight="700" fill="#FFB020">{_html.escape(full_label)}</text>'
            f'<text x="0" y="-25" text-anchor="middle" font-family="Inter, sans-serif" '
            f'font-size="6" fill="#FFE1A8">{tip_text}</text>'
            f'</g></g>'
        )

    defs = """
    <defs>
        <marker id="arrowGreen" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#00E676"/></marker>
        <marker id="arrowOrange" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#FFB020"/></marker>
        <marker id="arrowBlue" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3B82F6"/></marker>
    </defs>
    """

    svg_content = (
        f'{defs}'
        f'<path d="{country_path}" fill="#16211A" stroke="rgba(0,230,118,0.35)" stroke-width="1.2" />'
        f'{lines_svg}{nodes_svg}'
    )

    style_block = """
    <style>
        .mine-pulse { animation: gtPulse 3s ease-in-out infinite; transform-origin: center; transform-box: fill-box; }
        @keyframes gtPulse { 0%,100% { opacity:0.45; transform:scale(1);} 50% { opacity:0.1; transform:scale(1.7);} }
        .mine-tip { opacity: 0; transition: opacity 150ms ease; pointer-events: none; }
        .mine-node:hover .mine-tip { opacity: 1; }
        .mine-node:hover .mine-label { opacity: 0; transition: opacity 100ms ease; }
        .mine-node { cursor: pointer; }
    </style>
    """

    html_doc = f"""
    <div style="position:relative;width:100%;height:{height}px;
        background:#0B1310;border:1px solid rgba(0,230,118,0.16);border-radius:16px;
        overflow:hidden;box-shadow:0 0 22px rgba(0,230,118,0.06);">
        <svg viewBox="435 95 235 235" style="width:100%;height:100%;display:block;">
            {svg_content}
        </svg>
    </div>
    {style_block}
    """
    components.html(html_doc, height=height + 10)