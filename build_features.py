#!/usr/bin/env python3
"""
build_features.py - Step 3: Feature engineering and position group splitting.

Processes Premier League player data from merged/merged_players.xlsx:
  1. Maps the 'Pos' column into 4 distinct position groups:
     - goalkeeper
     - defender
     - midfielder
     - forward
  2. Flags low-sample players (Min < 90) via a boolean 'low_sample' column.
  3. Identifies raw volume/counting stats and converts them to per-90 rates (value / 90s),
     safely handling 0 or null 90s without errors.
  4. Preserves both raw counting stats and new per-90 columns.
  5. Splits players into 4 position-specific sheets in features/player_features.xlsx:
     - goalkeepers: shared identity columns + goalkeeping per-90s + save/clean sheet rates
     - defenders, midfielders, forwards: shared identity columns + outfield per-90 stats
       (skipping entirely null per-90 columns for that group).
  6. Prints a comprehensive validation and summary report.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd


INPUT_FILE_DEFAULT = Path("merged/merged_players.xlsx")
OUTPUT_FILE_DEFAULT = Path("features/player_features.xlsx")

# Shared identity columns included on every position sheet
SHARED_IDENTITY_COLUMNS: list[str] = [
    "Player",
    "club",
    "Pos",
    "position_group",
    "Age",
    "Min",
    "90s",
    "low_sample",
]

# Raw counting volume columns identified in merged_players.xlsx
COUNTING_STAT_COLUMNS: list[str] = [
    # Standard table counting stats
    "Gls",      # Goals scored
    "Ast",      # Assists
    "G+A",      # Goals + Assists
    "G-PK",     # Non-penalty goals
    "PK",       # Penalty kicks scored
    "PKatt",    # Penalty kicks attempted
    "CrdY",     # Yellow cards
    "CrdR",     # Red cards
    # Shooting table counting stats
    "Sh",       # Total shots
    "SoT",      # Shots on target
    # Miscellaneous table counting stats
    "2CrdY",    # Second yellow cards
    "Fls",      # Fouls committed
    "Fld",      # Fouls drawn
    "Off",      # Offsides
    "Crs",      # Crosses
    "Int",      # Interceptions
    "TklW",     # Tackles won
    "PKwon",    # Penalty kicks won
    "PKcon",    # Penalty kicks conceded
    "OG",       # Own goals
    # Playing time table counting stats
    "onG",      # Team goals scored while player on pitch
    "onGA",     # Team goals conceded while player on pitch
    # Goalkeeping table counting stats
    "GA",       # Goals against
    "SoTA",     # Shots on target against
    "Saves",    # Saves made
    "CS",       # Clean sheets
    "W",        # Wins
    "D",        # Draws
    "L",        # Losses
    "PKA",      # Penalty kicks allowed
    "PKsv",     # Penalty kicks saved
    "PKm",      # Penalty kicks missed by opponent
]

# Goalkeeping rate / percentage metrics to retain on goalkeepers sheet
GOALKEEPER_RATES: list[str] = [
    "Save%",    # Save percentage
    "CS%",      # Clean sheet percentage
    "GA90",     # Goals against per 90 from source
    "Save%.1",  # Penalty kick save percentage
]


def map_position_group(pos: str) -> str:
    """
    Maps raw Pos values (including hybrids like DF,MF, MF,FW, FW,MF) to position groups:
      - If Pos contains 'GK' -> 'goalkeeper'
      - Otherwise, takes the first position code listed:
          'DF' -> 'defender'
          'MF' -> 'midfielder'
          'FW' -> 'forward'
    """
    if pd.isna(pos):
        return "unknown"
    p = str(pos).strip().upper()
    if "GK" in p:
        return "goalkeeper"

    # Split by commas, slashes, or whitespace to extract the primary position code
    tokens = re.split(r"[,/\s]+", p)
    primary_code = tokens[0][:2] if tokens else ""

    if primary_code == "DF":
        return "defender"
    elif primary_code == "MF":
        return "midfielder"
    elif primary_code == "FW":
        return "forward"
    return "unknown"


def add_position_and_sample_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds 'position_group' and 'low_sample' columns:
      - position_group: 'goalkeeper', 'defender', 'midfielder', 'forward'
      - low_sample: True if Min < 90 (or Min is NaN/0), False otherwise.
    """
    df_mod = df.copy()
    df_mod["position_group"] = df_mod["Pos"].apply(map_position_group)

    # Players with NaN minutes played 0 minutes (< 90)
    df_mod["low_sample"] = df_mod["Min"].fillna(0.0) < 90.0
    return df_mod


def compute_per90_columns(
    df: pd.DataFrame,
    counting_cols: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """
    Computes <col>_per90 = value / 90s for every identified counting stat.
    Safely assigns NaN when 90s is 0, NaN, or the stat is NaN.
    Preserves all original columns.

    Returns:
        (df_with_features, created_per90_cols)
    """
    df_feat = df.copy()
    created_cols: list[str] = []

    # Valid mask where 90s is strictly positive and non-null
    valid_90s = df_feat["90s"].notna() & (df_feat["90s"] > 0)

    for col in counting_cols:
        if col not in df_feat.columns:
            continue
        per90_col_name = f"{col}_per90"
        created_cols.append(per90_col_name)

        # Condition: both 90s is valid and the stat itself is non-null
        stat_valid = valid_90s & df_feat[col].notna()

        # Vectorized safe division
        df_feat[per90_col_name] = np.where(
            stat_valid,
            df_feat[col].astype(float) / df_feat["90s"].astype(float),
            np.nan,
        )

    return df_feat, created_cols


def prepare_position_sheets(
    df_features: pd.DataFrame,
    created_per90_cols: list[str],
) -> dict[str, pd.DataFrame]:
    """
    Splits df_features into 4 separate position sheets:
      1. 'goalkeepers'
      2. 'defenders'
      3. 'midfielders'
      4. 'forwards'

    Each sheet includes:
      - Shared identity columns (Player, club, Pos, position_group, Age, Min, 90s, low_sample)
      - Relevant per-90 stat columns (skipping entirely null columns for that group)
      - Goalkeepers additionally include goalkeeping rates (Save%, CS%, GA90, Save%.1).
    """
    sheets: dict[str, pd.DataFrame] = {}

    # Define prefixes/sets for goalkeeping metrics
    gk_per90_prefixes = ("GA_", "SoTA_", "Saves_", "CS_", "W_", "D_", "L_", "PKA_", "PKsv_", "PKm_")
    gk_per90_cols = [c for c in created_per90_cols if c.startswith(gk_per90_prefixes)]
    outfield_per90_cols = [c for c in created_per90_cols if not c.startswith(gk_per90_prefixes)]

    sheet_specs = [
        ("goalkeepers", "goalkeeper", True),
        ("defenders", "defender", False),
        ("midfielders", "midfielder", False),
        ("forwards", "forward", False),
    ]

    for sheet_name, group_code, is_gk in sheet_specs:
        group_df = df_features[df_features["position_group"] == group_code].copy()

        if is_gk:
            # Goalkeeper per-90 metrics (skipping entirely null ones)
            active_gk_per90 = [c for c in gk_per90_cols if group_df[c].notna().any()]

            # Goalkeeper rate metrics present in the table
            active_gk_rates = [c for c in GOALKEEPER_RATES if c in group_df.columns and group_df[c].notna().any()]

            selected_cols = SHARED_IDENTITY_COLUMNS + active_gk_per90 + active_gk_rates
        else:
            # Outfield per-90 metrics (skipping entirely null ones, e.g. PKwon_per90, PKcon_per90)
            active_outfield_per90 = [c for c in outfield_per90_cols if group_df[c].notna().any()]

            selected_cols = SHARED_IDENTITY_COLUMNS + active_outfield_per90

        # Subset DataFrame to selected columns
        sheets[sheet_name] = group_df[selected_cols].copy()

    return sheets


def save_player_features(
    sheets: dict[str, pd.DataFrame],
    output_path: Path,
) -> None:
    """
    Saves the 4 position sheets to a single Excel workbook using openpyxl.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, sheet_df in sheets.items():
            sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)


def print_reports(
    df_raw: pd.DataFrame,
    df_features: pd.DataFrame,
    counting_cols: list[str],
    sheets: dict[str, pd.DataFrame],
    output_path: Path,
) -> None:
    """
    Prints the required reports:
      1. Position group mapping review (counts & distinct raw Pos mappings).
      2. Identified counting stats list before conversion.
      3. Final summary: row count per sheet and list of per-90 columns contained in each sheet.
    """
    print("\n" + "=" * 75)
    print(" PREMIER LEAGUE 2025-26 FEATURE ENGINEERING REPORT")
    print("=" * 75)

    print("\n📋 1. Position Group Mapping Review (Pos -> position_group):")
    # Show distinct raw Pos values and mapped groups
    pos_map_review = (
        df_features[["Pos", "position_group"]]
        .drop_duplicates()
        .sort_values(by="Pos")
    )
    for _, row in pos_map_review.iterrows():
        print(f"   • Raw Pos: {row['Pos']:8s}  ->  position_group: '{row['position_group']}'")

    print("\n📊 Position Group Player Counts:")
    counts = df_features["position_group"].value_counts()
    for grp, cnt in counts.items():
        print(f"   • {grp:12s} : {cnt:3d} players")
    print(f"   • {'TOTAL':12s} : {len(df_features):3d} players")

    print("\n⏱️  2. Low Sample Flag Distribution (Min < 90 mins):")
    low_sample_counts = df_features["low_sample"].value_counts()
    print(f"   • low_sample == True  (< 90 mins)  : {low_sample_counts.get(True, 0):3d} players")
    print(f"   • low_sample == False (>= 90 mins) : {low_sample_counts.get(False, 0):3d} players")

    print(f"\n🔢 3. Identified Counting Stats for Per-90 Conversion ({len(counting_cols)} columns):")
    for col in counting_cols:
        non_null_cnt = df_raw[col].notna().sum() if col in df_raw.columns else 0
        print(f"   • {col:10s} -> {col + '_per90':16s} (valid values in raw data: {non_null_cnt})")

    print(f"\n💾 4. Output Workbook: {output_path}")
    print("=" * 75)
    print(" POSITION SHEETS SUMMARY:")
    print("=" * 75)

    for sheet_name, sheet_df in sheets.items():
        per90_in_sheet = [c for c in sheet_df.columns if c.endswith("_per90")]
        rate_in_sheet = [c for c in sheet_df.columns if c in GOALKEEPER_RATES]
        print(f"\n📑 Sheet: '{sheet_name}'")
        print(f"   • Row count   : {len(sheet_df)} players")
        print(f"   • Column count: {len(sheet_df.columns)} columns")
        print(f"   • Per-90 stat columns ({len(per90_in_sheet)}):")
        for c in per90_in_sheet:
            print(f"      - {c}")
        if rate_in_sheet:
            print(f"   • Goalkeeper rate columns ({len(rate_in_sheet)}):")
            for c in rate_in_sheet:
                print(f"      - {c}")

    print("\n" + "=" * 75 + "\n")


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert counting stats to per-90 rates and split into position group sheets."
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        default=INPUT_FILE_DEFAULT,
        help="Path to merged_players.xlsx (default: 'merged/merged_players.xlsx').",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=OUTPUT_FILE_DEFAULT,
        help="Path to output player_features.xlsx (default: 'features/player_features.xlsx').",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    input_file: Path = args.input_file
    output_file: Path = args.output_file

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}. Please run merge_players.py first.")

    print(f"Loading merged dataset from: {input_file}...")
    df_raw = pd.read_excel(input_file)
    print(f"Loaded {len(df_raw)} players across {len(df_raw.columns)} columns.")

    # Step 2 & 3: Map position groups and add low_sample flag
    df_prepped = add_position_and_sample_flags(df_raw)

    # Step 4, 5, 6: Identify counting stats and compute per-90 values
    counting_cols = [c for c in COUNTING_STAT_COLUMNS if c in df_prepped.columns]
    df_features, created_per90_cols = compute_per90_columns(df_prepped, counting_cols)

    # Step 7: Split into 4 position sheets with relevant columns
    sheets = prepare_position_sheets(df_features, created_per90_cols)

    # Save to features/player_features.xlsx
    print(f"Saving sheets to: {output_file}...")
    save_player_features(sheets, output_file)
    print("Save complete.")

    # Step 8: Print validation and summary report
    print_reports(df_raw, df_features, counting_cols, sheets, output_file)


if __name__ == "__main__":
    main()
