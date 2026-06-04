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

    Key step: auto-map column names from any real Excel file to the
    canonical names expected by config.COLUMNS using case-insensitive
    alias matching. Handles 'location', 'LOCATION', 'Site', 'Plant', etc.
    """
    if df.empty:
        return df

    df = df.copy()

    # Step 1: Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    # Step 2: Smart case-insensitive column auto-mapping
    # canonical name -> list of acceptable lowercase aliases
    COLUMN_ALIASES = {
        "Asset ID"       : ["asset id", "assetid", "asset_id", "id", "tag",
                            "asset tag", "asset no", "asset number", "ci id"],
        "Name"           : ["name", "asset name", "item name", "description",
                            "title", "ci name", "hostname", "device name"],
        "Class"          : ["class", "asset class", "category", "asset type",
                            "asset category", "class name"],
        "Location"       : ["location", "site", "plant", "facility", "office",
                            "location name", "site name", "place", "building"],
        "Sublocation"    : ["sublocation", "sub location", "sub-location", "floor",
                            "room", "area", "zone", "subloc"],
        "Region"         : ["region", "zone", "geography", "geo", "territory",
                            "region name"],
        "Custodian"      : ["custodian", "owner", "user", "assigned to",
                            "assignee", "responsible", "custodian name",
                            "asset owner", "emp id", "employee", "managed by"],
        "Team"           : ["team", "team name", "group", "it team"],
        "Support Group"  : ["support group", "support team", "support",
                            "helpdesk", "resolver group"],
        "Department"     : ["department", "dept", "business unit", "division",
                            "department name", "cost centre", "cost center"],
        "CI Type"        : ["ci type", "ci_type", "configuration item type",
                            "item type", "device type", "asset subtype"],
        "Hardware Status": ["hardware status", "status", "state", "condition",
                            "asset status", "operational status", "hw status",
                            "lifecycle", "lifecycle status"],
        "Manufacturer"   : ["manufacturer", "make", "brand", "vendor", "oem",
                            "manufacturer name", "mfr"],
        "Company"        : ["company", "organisation", "organization", "org",
                            "entity", "company name", "business"],
        "Installed On"   : ["installed on", "install date", "installation date",
                            "date installed", "purchase date", "commissioned",
                            "commission date", "created on", "created date",
                            "deployment date", "deployed on"],
        "Asset Criteria" : ["asset criteria", "criteria", "priority", "criticality",
                            "asset criticality", "importance", "tier",
                            "classification"],
    }

    alias_map = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            alias_map[alias] = canonical

    rename_dict = {}
    for col in list(df.columns):
        col_lower = col.lower().strip()
        if col_lower in alias_map:
            target = alias_map[col_lower]
            if target not in df.columns and col != target:
                rename_dict[col] = target

    if rename_dict:
        df.rename(columns=rename_dict, inplace=True)
        logger.info("Auto-mapped columns: %s", rename_dict)

    # Step 3: Strip whitespace from string cell values
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        try:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"nan": np.nan, "None": np.nan, "<NA>": np.nan})
        except Exception:
            pass

    # Step 4: Parse date columns
    date_candidates = [
        c for c in df.columns
        if any(kw in c.lower() for kw in
               ("date", "install", "created", "updated", "on", "commission"))
    ]
    for col in date_candidates:
        try:
            parsed = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
            if parsed.notna().mean() > 0.20:   # accept if 20%+ rows parsed OK
                df[col] = parsed
        except Exception:
            pass

    # Step 5: Derive helper date columns from 'Installed On'
    io_col = COLUMNS["installed_on"]
    if io_col in df.columns and pd.api.types.is_datetime64_any_dtype(df[io_col]):
        df["_install_year"]       = df[io_col].dt.year
        df["_install_month"]      = df[io_col].dt.month
        df["_install_month_name"] = df[io_col].dt.strftime("%b")
        try:
            df["_install_quarter"] = df[io_col].dt.to_period("Q").astype(str)
            df["_install_ym"]      = df[io_col].dt.to_period("M").astype(str)
        except Exception:
            df["_install_quarter"] = (
                df[io_col].dt.year.astype(str) + "-Q"
                + df[io_col].dt.quarter.astype(str)
            )
            df["_install_ym"] = df[io_col].dt.strftime("%Y-%m")

    # Step 6: Replace remaining blank strings with NaN
    df.replace(r"^\s*$", np.nan, regex=True, inplace=True)

    logger.info("Normalised: %d rows x %d cols | cols: %s",
                df.shape[0], df.shape[1], list(df.columns))
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
