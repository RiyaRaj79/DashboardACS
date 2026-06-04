# =============================================================================
# database.py - Database / Data Loading Layer
# =============================================================================
"""
Handles:
  - Loading data from Excel (.xlsx / .xls)
  - Loading from CSV
  - Loading from SQLite via SQLAlchemy
  - Schema introspection
  - Data type normalisation
"""

import os
import io
import hashlib
import logging
import pandas as pd
import numpy as np
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

import streamlit as st
from config import (
    DEFAULT_EXCEL_PATH, SQLITE_DB_PATH,
    COLUMNS, CACHE_TTL
)

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger("database")


# ===========================================================================
# DATA LOADING
# ===========================================================================

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_excel(file_path: str) -> pd.DataFrame:
    """Load and normalise an Excel file from *file_path*."""
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
        logger.info("Loaded %d rows from '%s'", len(df), file_path)
        return _normalise(df)
    except FileNotFoundError:
        logger.warning("Excel file not found: %s", file_path)
        return pd.DataFrame()
    except Exception as exc:
        logger.error("Failed to load Excel: %s", exc)
        st.error(f"❌ Error loading Excel file: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_from_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Load data from an uploaded file (bytes). Supports .xlsx/.xls and .csv."""
    try:
        ext = os.path.splitext(filename)[-1].lower()
        if ext in (".xlsx", ".xls"):
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
        elif ext == ".csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            st.error(f"Unsupported file type: {ext}")
            return pd.DataFrame()
        logger.info("Loaded %d rows from uploaded file '%s'", len(df), filename)
        return _normalise(df)
    except Exception as exc:
        logger.error("Failed to load uploaded file: %s", exc)
        st.error(f"❌ Error loading file: {exc}")
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# SQLAlchemy helpers
# ---------------------------------------------------------------------------

def get_engine(connection_string: str) -> sa.engine.Engine:
    """Return a SQLAlchemy engine for the given *connection_string*."""
    try:
        engine = sa.create_engine(connection_string, pool_pre_ping=True)
        with engine.connect():
            pass
        logger.info("DB connection established: %s", connection_string[:60])
        return engine
    except Exception as exc:
        logger.error("DB connection failed: %s", exc)
        st.error(f"❌ Database connection error: {exc}")
        return None


def get_sqlite_engine() -> sa.engine.Engine:
    """Return a SQLite engine pointing at the local asset DB."""
    return get_engine(f"sqlite:///{SQLITE_DB_PATH}")


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_from_db(connection_string: str, table_name: str) -> pd.DataFrame:
    """Load an entire table from a SQL database."""
    engine = get_engine(connection_string)
    if engine is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql_table(table_name, engine)
        return _normalise(df)
    except Exception as exc:
        logger.error("Failed to load table '%s': %s", table_name, exc)
        st.error(f"❌ Error loading table: {exc}")
        return pd.DataFrame()


def list_tables(connection_string: str) -> list:
    """Return the list of table names in the database."""
    engine = get_engine(connection_string)
    if engine is None:
        return []
    try:
        inspector = sa_inspect(engine)
        return inspector.get_table_names()
    except Exception as exc:
        logger.error("Failed to list tables: %s", exc)
        return []


def save_to_sqlite(df: pd.DataFrame, table_name: str = "it_assets") -> bool:
    """Persist *df* to the local SQLite database."""
    try:
        os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
        engine = get_sqlite_engine()
        if engine is None:
            return False
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        logger.info("Saved %d rows to SQLite table '%s'", len(df), table_name)
        return True
    except Exception as exc:
        logger.error("Failed to save to SQLite: %s", exc)
        return False


# ===========================================================================
# DATA NORMALISATION
# ===========================================================================

def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean, cast, and standardise columns so the rest of the app
    can rely on consistent dtypes and names.
    """
    if df.empty:
        return df

    df = df.copy()

    # Strip leading / trailing whitespace from string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda s: s.str.strip() if s.dtype == "O" else s)

    # Normalise column names: strip & replace spaces with original names
    df.columns = [str(c).strip() for c in df.columns]

    # Attempt to parse 'Installed On' (or similar) as datetime
    date_candidates = [
        c for c in df.columns
        if any(kw in c.lower() for kw in ("date", "install", "created", "updated", "on"))
    ]
    for col in date_candidates:
        try:
            df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
        except Exception:
            pass

    # Derive helper date columns from 'Installed On'
    if COLUMNS["installed_on"] in df.columns:
        io_col = COLUMNS["installed_on"]
        df["_install_year"]    = df[io_col].dt.year
        df["_install_month"]   = df[io_col].dt.month
        df["_install_month_name"] = df[io_col].dt.strftime("%b")
        df["_install_quarter"] = df[io_col].dt.to_period("Q").astype(str)
        df["_install_ym"]      = df[io_col].dt.to_period("M").astype(str)

    # Replace blank / empty strings with NaN for uniformity
    df.replace(r"^\s*$", np.nan, regex=True, inplace=True)

    logger.info("Normalised DataFrame: %d rows × %d cols", *df.shape)
    return df


# ===========================================================================
# SCHEMA INSPECTION
# ===========================================================================

def get_schema_summary(df: pd.DataFrame) -> dict:
    """Return a structured summary of the dataframe schema."""
    if df.empty:
        return {}

    summary = {}
    for col in df.columns:
        dtype  = str(df[col].dtype)
        n_null = int(df[col].isna().sum())
        n_unique = int(df[col].nunique(dropna=True))
        summary[col] = {
            "dtype"   : dtype,
            "nulls"   : n_null,
            "unique"  : n_unique,
            "sample"  : df[col].dropna().head(3).tolist(),
        }
    return summary


# ===========================================================================
# DEMO DATA (fallback when no file is uploaded)
# ===========================================================================

def generate_demo_data(n: int = 204) -> pd.DataFrame:
    """
    Generate synthetic IT asset data that matches the expected schema.
    Used when no real Excel file is available.
    """
    rng = np.random.default_rng(42)

    locations = [
        "Jamshedpur Plant", "Mumbai Office", "Kolkata HQ",
        "Pune R&D Centre", "Delhi NCR Office", "Chennai Unit",
    ]
    sublocations = [
        "Server Room A", "IT Hub B", "Data Centre", "Floor 3",
        "Network Room", "Control Room", "Operations Bay",
    ]
    regions    = ["East", "West", "North", "South", "Central"]
    departments = [
        "IT Infrastructure", "Mechanical Engineering", "Procurement",
        "HR & Admin", "Finance", "Safety & Environment",
        "Steel Manufacturing", "R&D", "Quality Control", "Logistics",
    ]
    ci_types = [
        "Server", "Workstation", "Laptop", "Switch",
        "Router", "Firewall", "Storage Array", "UPS",
        "Printer", "IP Phone", "CCTV Camera", "Access Point",
    ]
    hw_statuses = [
        "Active", "Active", "Active", "Active",  # weighted heavily
        "In Maintenance", "Retired", "Spare", "Decommissioned",
    ]
    manufacturers = [
        "Dell", "HP", "Lenovo", "Cisco", "IBM",
        "Juniper", "Fortinet", "NetApp", "APC", "Poly",
    ]
    companies     = ["Tata Steel Ltd", "Tata Sons", "TCS", "External Vendor"]
    asset_classes = ["Hardware", "Network", "Peripherals", "Telecom", "Software Appliance"]
    asset_criteria= ["Critical", "Important", "Standard", "Non-Critical"]
    support_groups= ["L1 Support", "L2 Network", "L3 Infrastructure", "Vendor Support"]
    teams         = ["IT Ops", "Network Team", "Security", "Server Team", "Field Support"]

    n_locs     = len(locations)
    n_sub      = len(sublocations)
    n_reg      = len(regions)
    n_dept     = len(departments)
    n_ci       = len(ci_types)
    n_hw       = len(hw_statuses)
    n_mfr      = len(manufacturers)
    n_comp     = len(companies)
    n_cls      = len(asset_classes)
    n_crit     = len(asset_criteria)
    n_sg       = len(support_groups)
    n_teams    = len(teams)

    loc_idx  = rng.integers(0, n_locs,  n)
    dept_idx = rng.integers(0, n_dept,  n)

    install_days = rng.integers(0, 365 * 8, n)   # up to 8 years ago
    install_dates = pd.Timestamp("2017-01-01") + pd.to_timedelta(install_days, unit="D")

    custodians = [
        f"EMP{1000 + rng.integers(0, 80)}"
        for _ in range(n)
    ]

    df = pd.DataFrame({
        "Asset ID"        : [f"TSIT{10000 + i}" for i in range(n)],
        "Name"            : [f"{ci_types[rng.integers(0,n_ci)]}-{1000+i}" for i in range(n)],
        "Class"           : [asset_classes[rng.integers(0,n_cls)] for _ in range(n)],
        "Location"        : [locations[i] for i in loc_idx],
        "Sublocation"     : [sublocations[rng.integers(0,n_sub)] for _ in range(n)],
        "Region"          : [regions[rng.integers(0,n_reg)] for _ in range(n)],
        "Custodian"       : custodians,
        "Team"            : [teams[rng.integers(0,n_teams)] for _ in range(n)],
        "Support Group"   : [support_groups[rng.integers(0,n_sg)] for _ in range(n)],
        "Department"      : [departments[i] for i in dept_idx],
        "CI Type"         : [ci_types[rng.integers(0,n_ci)] for _ in range(n)],
        "Hardware Status" : [hw_statuses[rng.integers(0,n_hw)] for _ in range(n)],
        "Manufacturer"    : [manufacturers[rng.integers(0,n_mfr)] for _ in range(n)],
        "Company"         : [companies[rng.integers(0,n_comp)] for _ in range(n)],
        "Installed On"    : install_dates,
        "Asset Criteria"  : [asset_criteria[rng.integers(0,n_crit)] for _ in range(n)],
    })

    return _normalise(df)
