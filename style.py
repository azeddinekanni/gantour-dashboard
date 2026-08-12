import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root{
  --ocp-green: #009A44;
  --ocp-green-dark: #006838;
  --ocp-green-light: #B7E4C7;
  --ocp-green-pale: #E6F5EC;
  --ocp-bg: #F7F8FA;
  --ocp-white: #FFFFFF;
  --ocp-anthracite: #1E2227;
  --ocp-anthracite-2: #262B31;
  --ocp-orange: #F5A623;
  --ocp-orange-pale: #FDF1DC;
  --ocp-red: #D92D20;
  --ocp-red-pale: #FBEAE9;
  --ocp-blue: #3B82F6;
  --ocp-ink: #1E2227;
  --ocp-muted: #6B7280;
  --ocp-line: #E7E9EC;
  --radius: 14px;
  --shadow-sm: 0 1px 2px rgba(30,34,39,0.04), 0 1px 3px rgba(30,34,39,0.06);
  --shadow-md: 0 2px 8px rgba(30,34,39,0.06), 0 1px 2px rgba(30,34,39,0.04);
}

.stApp{
  background: var(--ocp-bg);
  font-family: 'Inter', sans-serif;
  color: var(--ocp-ink);
}

h1, h2, h3, h4{
  font-family: 'Inter', sans-serif;
  font-weight: 700 !important;
  letter-spacing: -0.3px;
  color: var(--ocp-ink);
}

section[data-testid="stSidebar"]{
  background: var(--ocp-anthracite);
}
section[data-testid="stSidebar"] *{
  color: #D8DBDE !important;
}

.login-wrapper{
  display:flex; justify-content:center; margin-top: 40px; margin-bottom: 10px;
}
.login-card{
  background: linear-gradient(115deg, rgba(0,104,56,0.92) 0%, rgba(30,34,39,0.95) 70%);
  border-radius: var(--radius);
  padding: 34px 40px;
  text-align:center;
  box-shadow: var(--shadow-md);
  width: 100%;
}
.login-title{ font-size: 26px; font-weight:800; color:#fff; letter-spacing:-0.4px; }
.login-subtitle{ font-size: 13.5px; color:#D8DBDE; margin-top:6px; }

.ocp-hero{
  position: relative;
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 22px;
  padding: 26px 32px;
  background:
    linear-gradient(115deg, rgba(0,104,56,0.88) 0%, rgba(30,34,39,0.92) 65%),
    repeating-linear-gradient(135deg, rgba(255,255,255,0.035) 0 2px, transparent 2px 28px),
    linear-gradient(135deg, #10261A 0%, #1E2227 100%);
  box-shadow: var(--shadow-md);
}
.ocp-hero-eyebrow{ color: var(--ocp-green-light); font-size:12.5px; font-weight:700; letter-spacing:1.2px; text-transform:uppercase; }
.ocp-hero-title{ font-size: 26px; font-weight: 800; color: #fff; letter-spacing: -0.4px; margin-top:6px; }
.ocp-hero-sub{ color:#C9CDD2; font-size:13.5px; margin-top:6px; max-width:760px; }

.kpi-card{
  background: var(--ocp-white);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--ocp-line);
  height: 100%;
}
.kpi-label{ font-size:12px; font-weight:600; color:var(--ocp-muted); text-transform:uppercase; letter-spacing:0.4px; }
.kpi-value{ font-size:26px; font-weight:800; color:var(--ocp-ink); margin-top:4px; font-family:'IBM Plex Mono', monospace; }
.kpi-delta-up{ color:var(--ocp-red); font-size:12.5px; font-weight:600; }
.kpi-delta-down{ color:var(--ocp-green); font-size:12.5px; font-weight:600; }

.section-card{
  background: var(--ocp-white);
  border-radius: var(--radius);
  padding: 20px 22px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--ocp-line);
  margin-bottom: 18px;
}

.badge{
  display:inline-block; padding: 3px 12px; border-radius:20px; font-size:12px; font-weight:700;
}
.badge-normal{ background: var(--ocp-green-pale); color: var(--ocp-green-dark); }
.badge-vigilance{ background: var(--ocp-orange-pale); color:#8A5A00; }
.badge-alerte{ background: var(--ocp-orange-pale); color:#8A5A00; }
.badge-critique{ background: var(--ocp-red-pale); color: var(--ocp-red); }
.badge-inconnu{ background: #ECEDEF; color: var(--ocp-muted); }

.alert-banner{
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 14px;
  font-size: 14px;
  font-weight:600;
  border-left: 6px solid;
}
.alert-critique{ background: var(--ocp-red-pale); border-color: var(--ocp-red); color: #7A1610; }
.alert-vigilance{ background: var(--ocp-orange-pale); border-color: var(--ocp-orange); color: #6B4600; }
.alert-normal{ background: var(--ocp-green-pale); border-color: var(--ocp-green); color: var(--ocp-green-dark); }

.data-issue{
  background:#FDF1DC; border-left: 5px solid var(--ocp-orange); border-radius:10px;
  padding: 12px 16px; font-size: 13px; color:#6B4600; margin-bottom:10px;
}
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