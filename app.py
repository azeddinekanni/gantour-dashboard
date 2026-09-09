from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from style import style_plotly
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

import style
import auth
import alerts
from data_loader import (
    build_mines_table, build_phase_table, get_data_issues,
    MINE_LABELS, PHASE_LABELS, MINE_VAR_LABELS, PHASE_VAR_LABELS_UC_US, PHASE_VAR_LABELS_UL
)

from pathlib import Path
from PIL import Image

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo_ocp.png"
page_icon = Image.open(LOGO_PATH) if LOGO_PATH.exists() else "🟢"

st.set_page_config(
    page_title="OCP Gantour Intelligence",
    page_icon=page_icon,
    layout="wide"
)

style.inject()

if not auth.check_authentication():
    st.stop()

mines_df = build_mines_table()
uc_df = build_phase_table("UC")
us_df = build_phase_table("US")
ul_df = build_phase_table("UL")

st.sidebar.markdown("### OCP Gantour Intelligence")
st.sidebar.markdown(f"**{st.session_state.full_name}**  \n{st.session_state.role}")
st.sidebar.divider()
auth.logout_button()
st.sidebar.divider()
st.sidebar.caption("Analyse econometrique des determinants des couts et modelisation predictive des couts operationnels sur la chaine de valeur miniere - Site Gantour")

tab_overview, tab_dist, tab_mines, tab_phases, tab_econometrics, tab_predict, tab_alerts = st.tabs(
    ["Vue d'ensemble", "Distribution des donnees", "Mines d'extraction", "Phases de traitement",
     "Analyse econometrique", "Modelisation predictive", "Objectifs & Alertes"]
)

with tab_overview:
    latest_date = mines_df["date"].max()
    last_30 = mines_df[mines_df["date"] > latest_date - pd.Timedelta(days=30)]
    prev_30 = mines_df[(mines_df["date"] <= latest_date - pd.Timedelta(days=30)) & (mines_df["date"] > latest_date - pd.Timedelta(days=60))]

    total_cost_30 = last_30["cout_total_mines"].sum()
    total_cost_prev = prev_30["cout_total_mines"].sum()
    cost_delta = ((total_cost_30 - total_cost_prev) / total_cost_prev * 100) if total_cost_prev else 0

    total_prod_30 = last_30["production_mines"].sum()
    total_prod_prev = prev_30["production_mines"].sum()
    prod_delta = ((total_prod_30 - total_prod_prev) / total_prod_prev * 100) if total_prod_prev else 0

    avg_unit_cost = last_30["cout_unitaire_mines"].mean()
    avg_unit_cost_prev = prev_30["cout_unitaire_mines"].mean() if len(prev_30) else np.nan
    unit_delta = ((avg_unit_cost - avg_unit_cost_prev) / avg_unit_cost_prev * 100) if avg_unit_cost_prev else 0

    n_sites = mines_df["mines"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        style.kpi_card("Cout total extraction (30j)", f"{total_cost_30:,.0f} DH", cost_delta, delta_positive_is_bad=True)
    with c2:
        style.kpi_card("Production totale (30j)", f"{total_prod_30:,.0f} t", prod_delta, delta_positive_is_bad=False)
    with c3:
        style.kpi_card("Cout unitaire moyen (30j)", f"{avg_unit_cost:,.2f} DH/t", unit_delta, delta_positive_is_bad=True)
    with c4:
        style.kpi_card("Sites d'extraction suivis", f"{n_sites}")

    st.markdown("")

    left, right = st.columns([2, 1])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Evolution du cout total d'extraction par mine")
        trend = mines_df.copy()
        trend["mois"] = trend["date"].dt.to_period("M").dt.to_timestamp()
        monthly = trend.groupby(["mois", "mine_label"])["cout_total_mines"].sum().reset_index()
        fig = px.line(monthly, x="mois", y="cout_total_mines", color="mine_label", markers=True,
                       color_discrete_sequence=["#009A44", "#3B82F6", "#F5A623"])
        fig.update_layout(height=380, legend_title_text="", xaxis_title="", yaxis_title="Cout total (DH)",
                           plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, l=10, r=10, b=10))
        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Repartition du cout total (30 derniers jours)")
        rep = last_30.groupby("mine_label")["cout_total_mines"].sum().reset_index()
        fig2 = px.pie(rep, values="cout_total_mines", names="mine_label", hole=0.55,
                       color_discrete_sequence=["#009A44", "#3B82F6", "#F5A623"])
        fig2.update_layout(height=380, margin=dict(t=10, l=10, r=10, b=10))
        fig2 = style_plotly(fig2)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Production journaliere par mine")
    fig3 = px.area(mines_df, x="date", y="production_mines", color="mine_label",
                    color_discrete_sequence=["#009A44", "#3B82F6", "#F5A623"])
    fig3.update_layout(height=340, legend_title_text="", xaxis_title="", yaxis_title="Production (t)",
                        plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, l=10, r=10, b=10))
    fig3 = style_plotly(fig3)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Etat des trois phases de traitement (30 derniers jours)")
    phase_cols = st.columns(3)
    for col, (code, dfp) in zip(phase_cols, [("UC", uc_df), ("US", us_df), ("UL", ul_df)]):
        last_p = dfp[dfp["date"] > dfp["date"].max() - pd.Timedelta(days=30)]
        with col:
            st.markdown(f"**{PHASE_LABELS[code]}**")
            st.metric("Production (30j)", f"{last_p['production'].sum():,.0f} t")
            st.metric("Cout unitaire moyen", f"{last_p['cout_unitaire'].mean():,.2f} DH/t")
    st.markdown('</div>', unsafe_allow_html=True)

with tab_dist:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Distribution statistique des variables")
    st.caption("Choisissez un perimetre (mine ou phase de traitement) puis une variable pour visualiser sa distribution, ses statistiques descriptives et detecter d'eventuelles valeurs atypiques.")

    scope = st.radio("Perimetre", ["Mines d'extraction", "Phases de traitement"], horizontal=True, key="dist_scope")

    if scope == "Mines d'extraction":
        mine_choice = st.selectbox("Site", options=list(MINE_LABELS.keys()), format_func=lambda x: MINE_LABELS[x], key="dist_mine")
        var_choice = st.selectbox("Variable", options=list(MINE_VAR_LABELS.keys()), format_func=lambda x: MINE_VAR_LABELS[x], key="dist_var_mine")
        series = mines_df[mines_df["mines"] == mine_choice][var_choice].dropna()
        var_label = MINE_VAR_LABELS[var_choice]
    else:
        phase_choice = st.selectbox("Phase", options=["UC", "US", "UL"], format_func=lambda x: PHASE_LABELS[x], key="dist_phase")
        phase_df_map = {"UC": uc_df, "US": us_df, "UL": ul_df}
        labels_map = PHASE_VAR_LABELS_UL if phase_choice == "UL" else PHASE_VAR_LABELS_UC_US
        var_choice = st.selectbox("Variable", options=list(labels_map.keys()), format_func=lambda x: labels_map[x], key="dist_var_phase")
        series = phase_df_map[phase_choice][var_choice].dropna()
        var_label = labels_map[var_choice]

    col_hist, col_box = st.columns([2, 1])
    with col_hist:
        fig_hist = px.histogram(series, nbins=40, color_discrete_sequence=["#009A44"])
        fig_hist.add_vline(x=series.mean(), line_dash="dash", line_color="#D92D20", annotation_text="Moyenne")
        fig_hist.add_vline(x=series.median(), line_dash="dot", line_color="#3B82F6", annotation_text="Mediane")
        fig_hist.update_layout(height=360, showlegend=False, xaxis_title=var_label, yaxis_title="Frequence",
                                plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, l=10, r=10, b=10))
        fig_hist = style_plotly(fig_hist)
        st.plotly_chart(fig_hist, use_container_width=True)
    with col_box:
        fig_box = px.box(series, points="outliers", color_discrete_sequence=["#009A44"])
        fig_box.update_layout(height=360, showlegend=False, yaxis_title=var_label,
                               plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, l=10, r=10, b=10))
        fig_box = style_plotly(fig_box)
        st.plotly_chart(fig_box, use_container_width=True)

    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower_fence, upper_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = series[(series < lower_fence) | (series > upper_fence)]

    stat_cols = st.columns(6)
    stats_values = [
        ("Moyenne", f"{series.mean():,.2f}"),
        ("Mediane", f"{series.median():,.2f}"),
        ("Ecart-type", f"{series.std():,.2f}"),
        ("Coef. variation", f"{(series.std() / series.mean() * 100):,.1f} %" if series.mean() else "N/A"),
        ("Asymetrie (skew)", f"{stats.skew(series):,.2f}"),
        ("Valeurs atypiques", f"{len(outliers)} ({len(outliers) / len(series) * 100:.1f} %)"),
    ]
    for col, (label, value) in zip(stat_cols, stats_values):
        with col:
            st.metric(label, value)

    with st.expander("Table descriptive complete"):
        desc = series.describe().to_frame(name=var_label)
        st.dataframe(desc, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

with tab_mines:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    mine_sel = st.selectbox("Site d'extraction", options=list(MINE_LABELS.keys()), format_func=lambda x: MINE_LABELS[x], key="mine_deep_dive")
    df_mine = mines_df[mines_df["mines"] == mine_sel].copy()

    if df_mine["eau_mines_estimee"].any():
        st.markdown(
            '<div class="data-issue">La consommation d\'eau de ce site est une estimation (donnee brute manquante dans la base d\'origine).</div>',
            unsafe_allow_html=True
        )

    var_ts = st.multiselect(
        "Variables a afficher (evolution journaliere)",
        options=[c for c in MINE_VAR_LABELS.keys() if c != "temperature"],
        default=["cout_total_mines", "production_mines"],
        format_func=lambda x: MINE_VAR_LABELS[x],
        key="mine_ts_vars"
    )
    if var_ts:
        fig_ts = go.Figure()
        colors = ["#009A44", "#3B82F6", "#F5A623", "#D92D20", "#6B4600", "#8A5A00", "#1E2227"]
        for i, v in enumerate(var_ts):
            fig_ts.add_trace(go.Scatter(x=df_mine["date"], y=df_mine[v], name=MINE_VAR_LABELS[v],
                                         line=dict(color=colors[i % len(colors)]), mode="lines"))
        fig_ts.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                              margin=dict(t=10, l=10, r=10, b=10), legend_title_text="")
        fig_ts = style_plotly(fig_ts)
        st.plotly_chart(fig_ts, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col_corr, col_scatter = st.columns(2)
    with col_corr:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Correlations entre determinants et cout")
        corr_cols = [c for c in MINE_VAR_LABELS.keys() if c not in ("cout_unitaire_mines",)]
        corr_matrix = df_mine[corr_cols].corr()
        corr_matrix.index = [MINE_VAR_LABELS[c] for c in corr_matrix.index]
        corr_matrix.columns = [MINE_VAR_LABELS[c] for c in corr_matrix.columns]
        fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdYlGn_r", zmin=-1, zmax=1, aspect="auto")
        fig_corr.update_layout(height=420, margin=dict(t=10, l=10, r=10, b=10))
        fig_corr = style_plotly(fig_corr)
        st.plotly_chart(fig_corr, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_scatter:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Relation determinant / cout total")
        determinant = st.selectbox(
            "Determinant",
            options=[c for c in MINE_VAR_LABELS.keys() if c not in ("cout_total_mines", "cout_unitaire_mines")],
            format_func=lambda x: MINE_VAR_LABELS[x],
            key="mine_scatter_det"
        )
        fig_sc = px.scatter(df_mine, x=determinant, y="cout_total_mines", trendline="ols",
                             color_discrete_sequence=["#009A44"], opacity=0.6)
        fig_sc.update_layout(height=420, xaxis_title=MINE_VAR_LABELS[determinant], yaxis_title="Cout total (DH)",
                              plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, l=10, r=10, b=10))
        fig_sc = style_plotly(fig_sc)
        st.plotly_chart(fig_sc, use_container_width=True)
        corr_val = df_mine[[determinant, "cout_total_mines"]].corr().iloc[0, 1]
        st.caption(f"Coefficient de correlation de Pearson : {corr_val:.3f}")
        st.markdown('</div>', unsafe_allow_html=True)

with tab_phases:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    phase_sel = st.selectbox("Phase de traitement", options=["UC", "US", "UL"], format_func=lambda x: PHASE_LABELS[x], key="phase_deep_dive")
    phase_map = {"UC": uc_df, "US": us_df, "UL": ul_df}
    label_map = {"UC": PHASE_VAR_LABELS_UC_US, "US": PHASE_VAR_LABELS_UC_US, "UL": PHASE_VAR_LABELS_UL}
    df_phase = phase_map[phase_sel]
    labels = label_map[phase_sel]

    var_ts_p = st.multiselect(
        "Variables a afficher (evolution journaliere)",
        options=list(labels.keys()),
        default=["cout_total", "production"],
        format_func=lambda x: labels[x],
        key="phase_ts_vars"
    )
    if var_ts_p:
        fig_ts_p = go.Figure()
        colors = ["#009A44", "#3B82F6", "#F5A623", "#D92D20", "#6B4600", "#8A5A00", "#1E2227", "#7A1610"]
        for i, v in enumerate(var_ts_p):
            fig_ts_p.add_trace(go.Scatter(x=df_phase["date"], y=df_phase[v], name=labels[v],
                                           line=dict(color=colors[i % len(colors)]), mode="lines"))
        fig_ts_p.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                                margin=dict(t=10, l=10, r=10, b=10), legend_title_text="")
        fig_ts_p = style_plotly(fig_ts_p)
        st.plotly_chart(fig_ts_p, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col_corr_p, col_scatter_p = st.columns(2)
    with col_corr_p:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Correlations entre intrants et cout")
        corr_cols_p = [c for c in labels.keys() if c != "cout_unitaire"]
        corr_matrix_p = df_phase[corr_cols_p].corr()
        corr_matrix_p.index = [labels[c] for c in corr_matrix_p.index]
        corr_matrix_p.columns = [labels[c] for c in corr_matrix_p.columns]
        fig_corr_p = px.imshow(corr_matrix_p, text_auto=".2f", color_continuous_scale="RdYlGn_r", zmin=-1, zmax=1, aspect="auto")
        fig_corr_p.update_layout(height=440, margin=dict(t=10, l=10, r=10, b=10))
        fig_corr_p = style_plotly(fig_corr_p)
        st.plotly_chart(fig_corr_p, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_scatter_p:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Relation intrant / cout total")
        determinant_p = st.selectbox(
            "Intrant",
            options=[c for c in labels.keys() if c not in ("cout_total", "cout_unitaire")],
            format_func=lambda x: labels[x],
            key="phase_scatter_det"
        )
        fig_sc_p = px.scatter(df_phase, x=determinant_p, y="cout_total", trendline="ols",
                               color_discrete_sequence=["#3B82F6"], opacity=0.6)
        fig_sc_p.update_layout(height=440, xaxis_title=labels[determinant_p], yaxis_title="Cout total (DH)",
                                plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, l=10, r=10, b=10))
        fig_sc_p = style_plotly(fig_sc_p)
        st.plotly_chart(fig_sc_p, use_container_width=True)
        corr_val_p = df_phase[[determinant_p, "cout_total"]].corr().iloc[0, 1]
        st.caption(f"Coefficient de correlation de Pearson : {corr_val_p:.3f}")
        st.markdown('</div>', unsafe_allow_html=True)

def run_ols(df, feature_cols, target_col, feature_labels):
    data = df[feature_cols + [target_col]].dropna()
    X = data[feature_cols]
    y = data[target_col]
    X_const = sm.add_constant(X)
    model = sm.OLS(y, X_const).fit()

    coef_table = pd.DataFrame({
        "Variable": ["Constante"] + [feature_labels[c] for c in feature_cols],
        "Coefficient": model.params.values,
        "Erreur standard": model.bse.values,
        "t-statistique": model.tvalues.values,
        "p-value": model.pvalues.values,
    })
    coef_table["Significatif (5%)"] = coef_table["p-value"].apply(lambda p: "Oui" if p < 0.05 else "Non")

    vif_data = pd.DataFrame()
    vif_data["Variable"] = [feature_labels[c] for c in feature_cols]
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]

    return model, coef_table, vif_data, data


with tab_econometrics:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Modelisation econometrique des determinants du cout")
    st.caption(
        "Regression lineaire multiple (Moindres Carres Ordinaires) du cout total sur les consommations "
        "physiques (determinants). Objectif : quantifier la contribution de chaque intrant a la formation du cout "
        "et identifier les variables statistiquement significatives."
    )

    econ_scope = st.radio("Perimetre d'analyse", ["Mines d'extraction", "Phases de traitement"], horizontal=True, key="econ_scope")

    if econ_scope == "Mines d'extraction":
        econ_mine = st.selectbox("Site", options=list(MINE_LABELS.keys()), format_func=lambda x: MINE_LABELS[x], key="econ_mine")
        df_econ = mines_df[mines_df["mines"] == econ_mine]
        target = "cout_total_mines"
        candidate_features = [c for c in MINE_VAR_LABELS.keys() if c not in ("cout_total_mines", "cout_unitaire_mines")]
        feat_labels = MINE_VAR_LABELS
        scope_label = MINE_LABELS[econ_mine]
    else:
        econ_phase = st.selectbox("Phase", options=["UC", "US", "UL"], format_func=lambda x: PHASE_LABELS[x], key="econ_phase")
        df_econ = {"UC": uc_df, "US": us_df, "UL": ul_df}[econ_phase]
        target = "cout_total"
        labels_e = PHASE_VAR_LABELS_UL if econ_phase == "UL" else PHASE_VAR_LABELS_UC_US
        candidate_features = [c for c in labels_e.keys() if c not in ("cout_total", "cout_unitaire")]
        feat_labels = labels_e
        scope_label = PHASE_LABELS[econ_phase]

    selected_features = st.multiselect(
        "Determinants a inclure dans le modele",
        options=candidate_features,
        default=candidate_features,
        format_func=lambda x: feat_labels[x],
        key="econ_features"
    )

    if len(selected_features) >= 1:
        model, coef_table, vif_data, data_used = run_ols(df_econ, selected_features, target, feat_labels)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("R2", f"{model.rsquared:.3f}")
        with m2:
            st.metric("R2 ajuste", f"{model.rsquared_adj:.3f}")
        with m3:
            st.metric("F-statistique", f"{model.fvalue:,.1f}")
        with m4:
            st.metric("Observations", f"{int(model.nobs)}")

        st.markdown("##### Coefficients estimes")
        st.dataframe(
            coef_table.style.format({"Coefficient": "{:,.4f}", "Erreur standard": "{:,.4f}",
                                      "t-statistique": "{:,.3f}", "p-value": "{:,.4f}"}),
            use_container_width=True
        )

        significant = coef_table[(coef_table["Variable"] != "Constante") & (coef_table["p-value"] < 0.05)]
        if len(significant) > 0:
            top_driver = significant.iloc[significant["Coefficient"].abs().argmax()]
            st.info(
                f"Le determinant le plus significatif du cout sur {scope_label} est **{top_driver['Variable']}** "
                f"(coefficient = {top_driver['Coefficient']:.3f}, p-value = {top_driver['p-value']:.4f}). "
                f"Une hausse d'une unite de cette variable est associee a une variation moyenne du cout total "
                f"de {top_driver['Coefficient']:.2f} DH, toutes choses egales par ailleurs."
            )
        else:
            st.warning("Aucun determinant n'est statistiquement significatif au seuil de 5% avec la selection actuelle.")

        col_vif, col_diag = st.columns(2)
        with col_vif:
            st.markdown("##### Multicolinearite (VIF)")
            st.caption("Un VIF > 5 signale une forte correlation entre determinants, a interpreter avec prudence.")
            st.dataframe(vif_data.style.format({"VIF": "{:,.2f}"}), use_container_width=True)
        with col_diag:
            st.markdown("##### Valeurs observees vs ajustees")
            fitted = model.fittedvalues
            fig_fit = px.scatter(x=data_used[target], y=fitted, labels={"x": "Cout observe", "y": "Cout ajuste"},
                                  color_discrete_sequence=["#009A44"], opacity=0.6)
            min_v, max_v = data_used[target].min(), data_used[target].max()
            fig_fit.add_trace(go.Scatter(x=[min_v, max_v], y=[min_v, max_v], mode="lines",
                                          line=dict(color="#D92D20", dash="dash"), name="Ajustement parfait"))
            fig_fit.update_layout(height=340, plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, l=10, r=10, b=10))
            fig_fit = style_plotly(fig_fit)
            st.plotly_chart(fig_fit, use_container_width=True)
    else:
        st.warning("Selectionnez au moins un determinant pour estimer le modele.")

    st.markdown('</div>', unsafe_allow_html=True)

with tab_predict:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Modelisation predictive des couts operationnels")
    st.caption(
        "Entrainement d'un modele predictif (regression lineaire ou foret aleatoire) pour anticiper le cout total "
        "a partir des consommations physiques journalieres, avec evaluation sur donnees non vues (jeu de test)."
    )

    pred_scope = st.radio("Perimetre", ["Mines d'extraction", "Phases de traitement"], horizontal=True, key="pred_scope")

    if pred_scope == "Mines d'extraction":
        pred_mine = st.selectbox("Site", options=list(MINE_LABELS.keys()), format_func=lambda x: MINE_LABELS[x], key="pred_mine")
        df_pred_source = mines_df[mines_df["mines"] == pred_mine]
        target_p = "cout_total_mines"
        candidate_p = [c for c in MINE_VAR_LABELS.keys() if c not in ("cout_total_mines", "cout_unitaire_mines")]
        labels_p = MINE_VAR_LABELS
        scope_label_p = MINE_LABELS[pred_mine]
    else:
        pred_phase = st.selectbox("Phase", options=["UC", "US", "UL"], format_func=lambda x: PHASE_LABELS[x], key="pred_phase")
        df_pred_source = {"UC": uc_df, "US": us_df, "UL": ul_df}[pred_phase]
        target_p = "cout_total"
        labels_p = PHASE_VAR_LABELS_UL if pred_phase == "UL" else PHASE_VAR_LABELS_UC_US
        candidate_p = [c for c in labels_p.keys() if c not in ("cout_total", "cout_unitaire")]
        scope_label_p = PHASE_LABELS[pred_phase]

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        model_choice = st.selectbox("Algorithme", ["Regression lineaire multiple", "Foret aleatoire (Random Forest)"], key="pred_algo")
    with col_b:
        test_size = st.slider("Part du jeu de test", 0.1, 0.4, 0.2, 0.05, key="pred_test_size")
    with col_c:
        selected_features_p = st.multiselect(
            "Variables explicatives", options=candidate_p, default=candidate_p, format_func=lambda x: labels_p[x], key="pred_features"
        )

    if len(selected_features_p) >= 1:
        data_p = df_pred_source[selected_features_p + [target_p]].dropna()
        X = data_p[selected_features_p]
        y = data_p[target_p]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

        if model_choice == "Regression lineaire multiple":
            model_p = LinearRegression()
        else:
            model_p = RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)

        model_p.fit(X_train, y_train)
        y_pred = model_p.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("R2 (test)", f"{r2:.3f}")
        with m2:
            st.metric("RMSE", f"{rmse:,.0f} DH")
        with m3:
            st.metric("MAE", f"{mae:,.0f} DH")
        with m4:
            st.metric("MAPE", f"{mape:.1f} %")

        col_pred, col_imp = st.columns([1.4, 1])
        with col_pred:
            st.markdown("##### Cout reel vs cout predit (jeu de test)")
            result_df = pd.DataFrame({"Reel": y_test.values, "Predit": y_pred}).reset_index(drop=True)
            fig_pred = go.Figure()
            fig_pred.add_trace(go.Scatter(y=result_df["Reel"], mode="lines+markers", name="Cout reel", line=dict(color="#1E2227")))
            fig_pred.add_trace(go.Scatter(y=result_df["Predit"], mode="lines+markers", name="Cout predit", line=dict(color="#009A44")))
            fig_pred.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white",
                                    margin=dict(t=10, l=10, r=10, b=10), xaxis_title="Observations (jeu de test)", yaxis_title="Cout total (DH)")
            fig_pred = style_plotly(fig_pred)
            st.plotly_chart(fig_pred, use_container_width=True)

        with col_imp:
            st.markdown("##### Importance des variables")
            if model_choice == "Regression lineaire multiple":
                importances = np.abs(model_p.coef_)
            else:
                importances = model_p.feature_importances_
            imp_df = pd.DataFrame({"Variable": [labels_p[c] for c in selected_features_p], "Importance": importances})
            imp_df = imp_df.sort_values("Importance", ascending=True)
            fig_imp = px.bar(imp_df, x="Importance", y="Variable", orientation="h", color_discrete_sequence=["#3B82F6"])
            fig_imp.update_layout(height=380, plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=10, l=10, r=10, b=10))
            fig_imp = style_plotly(fig_imp)
            st.plotly_chart(fig_imp, use_container_width=True)

        st.markdown("##### Simulation : prediction a partir de nouvelles valeurs")
        sim_cols = st.columns(len(selected_features_p) if len(selected_features_p) <= 4 else 4)
        sim_values = {}
        for i, feat in enumerate(selected_features_p):
            with sim_cols[i % len(sim_cols)]:
                default_val = float(data_p[feat].median())
                sim_values[feat] = st.number_input(labels_p[feat], value=default_val, key=f"sim_{feat}")
        sim_input = pd.DataFrame([sim_values])[selected_features_p]
        sim_prediction = model_p.predict(sim_input)[0]
        st.success(f"Cout total predit pour {scope_label_p} avec ces parametres : **{sim_prediction:,.0f} DH**")
    else:
        st.warning("Selectionnez au moins une variable explicative.")

    st.markdown('</div>', unsafe_allow_html=True)

with tab_alerts:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### Objectifs de production et limites de consommation")
    st.caption(
        "Definissez un objectif de production ou une limite journaliere de consommation pour un site ou une phase. "
        "Le systeme compare automatiquement la derniere valeur enregistree a ce seuil et declenche une alerte "
        "envoyee aux managers en cas de depassement."
    )

    alert_scope = st.radio("Perimetre", ["Mines d'extraction", "Phases de traitement"], horizontal=True, key="alert_scope")

    if alert_scope == "Mines d'extraction":
        alert_site = st.selectbox("Site", options=list(MINE_LABELS.keys()), format_func=lambda x: MINE_LABELS[x], key="alert_site")
        df_alert = mines_df[mines_df["mines"] == alert_site]
        labels_a = MINE_VAR_LABELS
        site_label_a = MINE_LABELS[alert_site]
    else:
        alert_phase = st.selectbox("Phase", options=["UC", "US", "UL"], format_func=lambda x: PHASE_LABELS[x], key="alert_phase")
        df_alert = {"UC": uc_df, "US": us_df, "UL": ul_df}[alert_phase]
        labels_a = PHASE_VAR_LABELS_UL if alert_phase == "UL" else PHASE_VAR_LABELS_UC_US
        site_label_a = PHASE_LABELS[alert_phase]

    var_a = st.selectbox("Variable a surveiller", options=list(labels_a.keys()), format_func=lambda x: labels_a[x], key="alert_var")
    is_production_target = "production" in var_a

    latest_row = df_alert.sort_values("date").iloc[-1]
    latest_value = latest_row[var_a]
    latest_date = latest_row["date"]
    historical_mean = df_alert[var_a].mean()
    historical_p90 = df_alert[var_a].quantile(0.9)

    col_cfg, col_status = st.columns([1, 1.3])
    with col_cfg:
        st.markdown("##### Configuration du seuil")
        mode = "min" if is_production_target else "max"
        default_limit = float(historical_p90) if mode == "max" else float(historical_mean)
        limit_value = st.number_input(
            f"{'Objectif minimum de production' if mode == 'min' else 'Limite journaliere maximale'} ({labels_a[var_a]})",
            value=round(default_limit, 2), key="alert_limit"
        )
        st.caption(f"Moyenne historique : {historical_mean:,.2f} - 90e centile : {historical_p90:,.2f}")
        recipients_raw = st.text_input("Emails des managers (separes par une virgule)", value="manager.gantour@ocpgroup.ma", key="alert_recipients")

    status, ratio = alerts.evaluate_threshold(latest_value, limit_value, mode=mode)

    with col_status:
        st.markdown("##### Etat actuel")
        st.markdown(
            f'<div class="alert-banner alert-{"critique" if status == "critique" else ("vigilance" if status in ("vigilance", "alerte") else "normal")}">'
            f'{site_label_a} - {labels_a[var_a]} : {latest_value:,.2f} le {latest_date.strftime("%d/%m/%Y")} '
            f'(seuil : {limit_value:,.2f}, ratio {ratio * 100:,.0f}%)'
            f'</div>',
            unsafe_allow_html=True
        )
        style.badge(status, alerts.STATUS_LABELS.get(status, status))

        fig_alert = go.Figure()
        fig_alert.add_trace(go.Scatter(x=df_alert["date"], y=df_alert[var_a], name=labels_a[var_a], line=dict(color="#1E2227")))
        fig_alert.add_hline(y=limit_value, line_dash="dash", line_color="#D92D20",
                             annotation_text="Objectif minimum" if mode == "min" else "Limite maximale")
        fig_alert.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white", margin=dict(t=30, l=10, r=10, b=10))
        fig_alert = style_plotly(fig_alert)
        st.plotly_chart(fig_alert, use_container_width=True)

    if status in ("alerte", "critique") or (mode == "min" and status in ("alerte", "critique")):
        st.markdown("##### Declenchement de l'alerte")
        if st.button("Envoyer l'alerte aux managers", key="send_alert_btn"):
            recipients = [r.strip() for r in recipients_raw.split(",") if r.strip()]
            subject, body = alerts.build_alert_message(site_label_a, labels_a[var_a], latest_value, limit_value, "", status)
            success, message = alerts.send_email_alert(recipients, subject, body)
            if success:
                st.success(message)
            else:
                st.warning(message)
            with st.expander("Apercu du message envoye"):
                st.text(f"Objet : {subject}\n\n{body}")

    st.markdown("##### Historique des jours de depassement")
    df_alert_hist = df_alert.copy()
    if mode == "max":
        df_alert_hist["depassement"] = df_alert_hist[var_a] > limit_value
    else:
        df_alert_hist["depassement"] = df_alert_hist[var_a] < limit_value
    n_depassements = df_alert_hist["depassement"].sum()
    st.write(f"Sur la periode analysee, **{n_depassements} jours sur {len(df_alert_hist)}** "
             f"({n_depassements / len(df_alert_hist) * 100:.1f}%) ont depasse le seuil configure.")
    if n_depassements > 0:
        st.dataframe(
            df_alert_hist[df_alert_hist["depassement"]][["date", var_a]].rename(
                columns={"date": "Date", var_a: labels_a[var_a]}
            ).sort_values("Date", ascending=False),
            use_container_width=True, height=220
        )

    st.markdown('</div>', unsafe_allow_html=True)