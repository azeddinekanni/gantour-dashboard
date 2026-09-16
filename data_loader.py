import streamlit as st
import pandas as pd
import numpy as np
import streamlit as st
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "data" / "Base_finale_Gantour.xlsx"

MINE_COLS = ["gasoil", "electricite_mine", "explosif", "eau_mines", "production_mines",
             "criblage", "vol_saute", "temperature", "cout_total_mines", "cout_unitaire_mines"]

UC_US_COLS = ["electricite_uc_us", "fuel", "fuel_litres", "gaz", "gazoline", "gazoline_litres",
              "production_uc_us", "cout_total_uc_us", "cout_unitaire_uc_us"]

UL_COLS = ["electricite_ul", "amine", "ester", "barrage", "step", "exhaure", "acp", "floculant",
           "prod_ul", "cout_total_ul", "cout_unitaire_ul"]

MINE_LABELS = {"BG": "Benguerir - Gantour (BG)", "MZ": "Mzinda (MZ)", "BO": "Bouchane (BO)"}
PHASE_LABELS = {"UC": "Calcination (UC)", "US": "Sechage (US)", "UL": "Laverie (UL)"}

DATA_ISSUES_LOG = []


@st.cache_data(show_spinner=False)
def load_raw():
    return pd.read_excel(DATA_PATH, sheet_name="Base Finale")


def _log_issue(message):
    if message not in DATA_ISSUES_LOG:
        DATA_ISSUES_LOG.append(message)


@st.cache_data(show_spinner=False)
def build_mines_table():
    raw = load_raw().copy()
    raw["date"] = pd.to_datetime(raw["date"])
    table = raw[["mines", "date"] + MINE_COLS].copy()

    missing_bo_eau = table[(table["mines"] == "BO") & (table["eau_mines"].isna())]
    if len(missing_bo_eau) > 0:
        ratio_ref = raw[raw["mines"].isin(["BG", "MZ"])]
        ratio = (ratio_ref["eau_mines"] / ratio_ref["production_mines"]).replace([np.inf, -np.inf], np.nan).dropna().mean()
        bo_mask = table["mines"] == "BO"
        estimated = table.loc[bo_mask, "production_mines"] * ratio
        table.loc[bo_mask, "eau_mines"] = table.loc[bo_mask, "eau_mines"].fillna(estimated)
        table["eau_mines_estimee"] = False
        table.loc[bo_mask, "eau_mines_estimee"] = True
        _log_issue(
            f"La consommation d'eau (eau_mines) du site Bouchane (BO) etait entierement absente "
            f"de la base ({len(missing_bo_eau)} jours). Elle a ete estimee a partir du ratio moyen "
            f"eau/production observe sur BG et MZ ({ratio:.3f} m3/t), applique a la production journaliere de BO."
        )
    else:
        table["eau_mines_estimee"] = False

    duplicated = table.duplicated(subset=["mines", "date"]).sum()
    if duplicated > 0:
        table = table.drop_duplicates(subset=["mines", "date"], keep="first")
        _log_issue(f"{duplicated} doublons (meme mine, meme date) ont ete supprimes.")

    for col in ["gasoil", "electricite_mine", "production_mines", "cout_total_mines"]:
        neg = (table[col] < 0).sum()
        if neg > 0:
            table.loc[table[col] < 0, col] = np.nan
            _log_issue(f"{neg} valeurs negatives detectees sur '{col}' et converties en donnee manquante.")

    table = table.sort_values(["mines", "date"]).reset_index(drop=True)
    table["mine_label"] = table["mines"].map(MINE_LABELS)
    return table


@st.cache_data(show_spinner=False)
def build_phase_table(phase_code):
    raw = load_raw().copy()
    raw["date"] = pd.to_datetime(raw["date"])

    if phase_code in ("UC", "US"):
        subset = raw[raw["phases_uc_us"] == phase_code][["date"] + UC_US_COLS].copy()
        rename_map = {
            "electricite_uc_us": "electricite", "production_uc_us": "production",
            "cout_total_uc_us": "cout_total", "cout_unitaire_uc_us": "cout_unitaire"
        }
        subset = subset.rename(columns=rename_map)
    else:
        subset = raw[raw["phase_ul"] == "UL"][["date"] + UL_COLS].copy()
        rename_map = {
            "electricite_ul": "electricite", "prod_ul": "production",
            "cout_total_ul": "cout_total", "cout_unitaire_ul": "cout_unitaire"
        }
        subset = subset.rename(columns=rename_map)

    value_cols = [c for c in subset.columns if c != "date"]
    for col in value_cols:
        before_na = subset[col].isna().sum()
        subset[col] = pd.to_numeric(subset[col], errors="coerce")
        after_na = subset[col].isna().sum()
        if after_na > before_na:
            _log_issue(
                f"{after_na - before_na} valeur(s) non numerique(s) detectee(s) dans la colonne '{col}' "
                f"de la phase {phase_code} et converties en donnee manquante."
            )

    subset = subset.sort_values("date").reset_index(drop=True)
    subset["phase"] = phase_code
    subset["phase_label"] = PHASE_LABELS[phase_code]
    return subset


@st.cache_data(show_spinner=False)
def get_data_issues():
    build_mines_table()
    build_phase_table("UC")
    build_phase_table("US")
    build_phase_table("UL")
    return list(DATA_ISSUES_LOG)


MINE_VAR_LABELS = {
    "gasoil": "Gasoil (litres)",
    "electricite_mine": "Electricite (kWh)",
    "explosif": "Explosif (kg)",
    "eau_mines": "Eau (m3)",
    "production_mines": "Production (t)",
    "criblage": "Criblage (t)",
    "vol_saute": "Volume saute (m3)",
    "temperature": "Temperature (C)",
    "cout_total_mines": "Cout total (DH)",
    "cout_unitaire_mines": "Cout unitaire (DH/t)",
}

PHASE_VAR_LABELS_UC_US = {
    "electricite": "Electricite (kWh)",
    "fuel": "Fuel (DH)",
    "fuel_litres": "Fuel (litres)",
    "gaz": "Gaz (DH)",
    "gazoline": "Gazoline (DH)",
    "gazoline_litres": "Gazoline (litres)",
    "production": "Production (t)",
    "cout_total": "Cout total (DH)",
    "cout_unitaire": "Cout unitaire (DH/t)",
}

PHASE_VAR_LABELS_UL = {
    "electricite": "Electricite (kWh)",
    "amine": "Amine (kg)",
    "ester": "Ester (kg)",
    "barrage": "Eau barrage (m3)",
    "step": "Eau STEP (m3)",
    "exhaure": "Eau exhaure (m3)",
    "acp": "ACP (kg)",
    "floculant": "Floculant (kg)",
    "production": "Production (t)",
    "cout_total": "Cout total (DH)",
    "cout_unitaire": "Cout unitaire (DH/t)",
}