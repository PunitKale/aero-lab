"""Immutable input manifest and explicit CSV validation."""
import hashlib,json
from pathlib import Path
import pandas as pd

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def manifest(directory: Path) -> dict:
    """Hash all CSV inputs in a release; timestamp metadata stays in records."""
    return {p.name:{"sha256":sha256(p),"bytes":p.stat().st_size} for p in sorted(directory.glob("*.csv"))}

def read_csv(path: Path,required: list[str]) -> pd.DataFrame:
    df=pd.read_csv(path)
    missing=set(required)-set(df)
    if missing: raise ValueError(f"Missing columns: {sorted(missing)}")
    if df[required].isna().any().any(): raise ValueError("Missing required data")
    return df
