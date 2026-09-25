"""
Veille marche : recuperation des prix externes qui influencent les couts
operationnels de Gantour (energie, intrants) et la valorisation du phosphate.

Sources :
- FRED (Federal Reserve Bank of St. Louis) : telechargement CSV public, sans cle API.
- Banque mondiale, Pink Sheet (CMO Historical Data Monthly) : fichier Excel.

Robustesse : chaque serie est recuperee independamment. En cas d'echec reseau,
on bascule sur la derniere copie locale (data/market/market_snapshot.csv),
afin que le dashboard reste utilisable hors ligne (ex. pendant la soutenance).
"""
import io
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data" / "market"
SNAPSHOT_PATH = DATA_DIR / "market_snapshot.csv"
WB_LOCAL_PATH = DATA_DIR / "CMO-Historical-Data-Monthly.xlsx"

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
HTTP_TIMEOUT = 20

# role = "cout"          -> une hausse est defavorable pour Gantour
# role = "valorisation"  -> une hausse est favorable (prix de vente du phosphate)
INDICATORS = {
    "brent": {
        "label": "Petrole Brent", "sub": "Energie des engins, sechage, calcination",
        "unit": "USD/baril", "source": "FRED", "series": "POILBREUSDM",
        "role": "cout", "icon": "🛢️",
    },
    "diesel": {
        "label": "Gasoil", "sub": "Carburant des engins miniers (prix US)",
        "unit": "USD/gallon", "source": "FRED", "series": "GASDESW",
        "role": "cout", "icon": "⛽",
    },
    "gaz_ue": {
        "label": "Gaz naturel Europe", "sub": "Energie thermique",
        "unit": "USD/MMBtu", "source": "FRED", "series": "PNGASEUUSDM",
        "role": "cout", "icon": "🔥",
    },
    "uree": {
        "label": "Uree", "sub": "Proxy du cout des explosifs (nitrate d'ammonium)",
        "unit": "USD/t", "source": "World Bank", "series": "Urea",
        "role": "cout", "icon": "💥",
    },
    "roche": {
        "label": "Roche phosphatee", "sub": "Prix de vente, f.o.b. Afrique du Nord",
        "unit": "USD/t", "source": "World Bank", "series": "Phosphate rock",
        "role": "valorisation", "icon": "🪨",
    },
    "dap": {
        "label": "DAP", "sub": "Phosphate diammonique (aval)",
        "unit": "USD/t", "source": "World Bank", "series": "DAP",
        "role": "valorisation", "icon": "⚫",
    },
    "acide_sulf": {
        "label": "PPI Acide sulfurique", "sub": "Aval : transformation Safi / Jorf",
        "unit": "Indice", "source": "FRED", "series": "WPU0613020T1",
        "role": "cout", "icon": "🧪",
    },
}


def _get_secret(name, default=None):
    """Lit une valeur dans st.secrets, puis dans les variables d'environnement."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


# ---------------------------------------------------------------- FRED
def _fetch_fred(series_id):
    resp = requests.get(FRED_CSV_URL.format(sid=series_id), timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    date_col, value_col = df.columns[0], df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")  # FRED code "." = manquant
    s = df.dropna().set_index(date_col)[value_col]
    # Harmonisation en frequence mensuelle (moyenne du mois)
    return s.resample("MS").mean().dropna()


# ---------------------------------------------------------------- Banque mondiale
def _read_world_bank_bytes():
    url = _get_secret("WB_PINK_SHEET_URL")
    if url:
        try:
            resp = requests.get(url, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp.content
        except Exception:
            pass
    if WB_LOCAL_PATH.exists():
        return WB_LOCAL_PATH.read_bytes()
    return None


def _parse_world_bank(content):
    raw = pd.read_excel(io.BytesIO(content), sheet_name="Monthly Prices", header=None)
    is_header = raw.apply(lambda r: r.astype(str).str.strip().eq("Phosphate rock").any(), axis=1)
    if not is_header.any():
        raise ValueError("En-tete 'Phosphate rock' introuvable dans le fichier Pink Sheet")
    header_idx = is_header[is_header].index[0]
    header = raw.iloc[header_idx].astype(str).str.strip()

    df = raw.iloc[header_idx + 1:].copy()
    df.columns = header
    parts = df.iloc[:, 0].astype(str).str.extract(r"(\d{4})M(\d{2})")
    df = df[parts.notna().all(axis=1)]
    parts = parts.loc[df.index]
    df.index = pd.to_datetime(parts[0] + "-" + parts[1] + "-01")
    return df


def _wb_column(df, name):
    for col in df.columns:
        if str(col).strip().lower() == name.lower():
            return col
    for col in df.columns:
        if str(col).strip().lower().startswith(name.lower()):
            return col
    return None


# ---------------------------------------------------------------- Point d'entree
@st.cache_data(ttl=24 * 3600, show_spinner=False)
def get_market_data():
    """
    Retourne (df, status) :
    - df : DataFrame long [date, cle, valeur] en frequence mensuelle
    - status : {cle: "direct" | "copie locale" | "indisponible"}
    """
    frames, status = [], {}

    wb_df = None
    wb_bytes = _read_world_bank_bytes()
    if wb_bytes:
        try:
            wb_df = _parse_world_bank(wb_bytes)
        except Exception:
            wb_df = None

    for key, meta in INDICATORS.items():
        try:
            if meta["source"] == "FRED":
                s = _fetch_fred(meta["series"])
            else:
                if wb_df is None:
                    raise RuntimeError("Pink Sheet indisponible")
                col = _wb_column(wb_df, meta["series"])
                if col is None:
                    raise KeyError(meta["series"])
                s = pd.to_numeric(wb_df[col], errors="coerce").dropna()
            if s.empty:
                raise ValueError("serie vide")
            frames.append(pd.DataFrame({"date": s.index, "cle": key, "valeur": s.values}))
            status[key] = "direct"
        except Exception:
            status[key] = "indisponible"

    live = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=["date", "cle", "valeur"])

    # Complement avec la copie locale pour les series indisponibles
    if SNAPSHOT_PATH.exists():
        try:
            snap = pd.read_csv(SNAPSHOT_PATH, parse_dates=["date"])
            missing = [k for k, v in status.items() if v == "indisponible"]
            fill = snap[snap["cle"].isin(missing)]
            if not fill.empty:
                live = pd.concat([live, fill], ignore_index=True)
                for k in fill["cle"].unique():
                    status[k] = "copie locale"
        except Exception:
            pass

    # Mise a jour de la copie locale avec les donnees fraiches
    if frames:
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            live.to_csv(SNAPSHOT_PATH, index=False)
        except Exception:
            pass

    live["date"] = pd.to_datetime(live["date"])
    return live.sort_values(["cle", "date"]).reset_index(drop=True), status


def series_for(df, key):
    sub = df[df["cle"] == key]
    return pd.Series(sub["valeur"].values, index=sub["date"]).sort_index()
