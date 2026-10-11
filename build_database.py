#!/usr/bin/env python3
"""
build_database.py - Step 4: Final database ingestion for Premier League Dashboard.

Loads player feature sheets from features/player_features.xlsx and builds
a SQLite database at data/pl_dashboard.db:
  1. Writes the 4 position-group sheets into tables:
     - goalkeepers
     - defenders
     - midfielders
     - forwards
  2. Creates a 5th table, 'all_players', containing only shared identity columns:
     - Player, club, Pos, position_group, Age, Min, 90s, low_sample
  3. Creates database indexes on (Player) and (club) for every table.
  4. Runs an automated verification pass confirming row counts, cross-table
     consistency, and a spot-check for Erling Haaland.
  5. Prints a comprehensive summary report with file size and verification details.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


FEATURES_FILE_DEFAULT = Path("features/player_features.xlsx")
DATABASE_FILE_DEFAULT = Path("data/pl_dashboard.db")

POSITION_SHEETS: list[str] = [
    "goalkeepers",
    "defenders",
    "midfielders",
    "forwards",
]

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


def load_feature_sheets(excel_path: Path) -> dict[str, pd.DataFrame]:
    """
    Loads all 4 position-group sheets from player_features.xlsx.
    """
    if not excel_path.exists():
        raise FileNotFoundError(
            f"Features file not found at: {excel_path}. Please run build_features.py first."
        )

    sheets: dict[str, pd.DataFrame] = {}
    for sheet_name in POSITION_SHEETS:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        sheets[sheet_name] = df

    return sheets


def build_all_players_table(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Builds the combined 'all_players' table containing only the shared identity columns:
    Player, club, Pos, position_group, Age, Min, 90s, low_sample.
    """
    subsets: list[pd.DataFrame] = []
    for sheet_name in POSITION_SHEETS:
        df = sheets[sheet_name]
        # Validate that all shared columns exist
        missing = [c for c in SHARED_IDENTITY_COLUMNS if c not in df.columns]
        if missing:
            raise KeyError(
                f"Sheet '{sheet_name}' is missing required shared column(s): {missing}"
            )
        subsets.append(df[SHARED_IDENTITY_COLUMNS])

    all_players_df = pd.concat(subsets, ignore_index=True)
    return all_players_df


def save_tables_and_indexes(
    tables: dict[str, pd.DataFrame],
    db_path: Path,
) -> None:
    """
    Writes all tables to SQLite database and creates indexes on Player and club.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        for table_name, df in tables.items():
            # Write table exactly as structured without altering column names
            df.to_sql(table_name, conn, if_exists="replace", index=False)

            # Create fast lookup indexes on Player and club
            cursor = conn.cursor()
            cursor.execute(
                f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_player" ON "{table_name}" ("Player")'
            )
            cursor.execute(
                f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_club" ON "{table_name}" ("club")'
            )
        conn.commit()


def verify_database(
    db_path: Path,
    spot_check_player: str = "Erling Haaland",
) -> dict:
    """
    Performs verification pass:
      1. Reads row count from each table.
      2. Validates that sum of position tables equals 693 and matches all_players.
      3. Verifies indexes exist for each table.
      4. Spot-checks that the target player exists in both their position table and all_players
         with identical Min values.
    """
    results: dict = {
        "table_counts": {},
        "indexes": [],
        "sum_position_tables": 0,
        "all_players_count": 0,
        "counts_match": False,
        "spot_check": {},
    }

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check all tables and row counts
        all_table_names = POSITION_SHEETS + ["all_players"]
        for table_name in all_table_names:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            results["table_counts"][table_name] = count

        position_sum = sum(
            results["table_counts"][s] for s in POSITION_SHEETS
        )
        all_players_count = results["table_counts"]["all_players"]
        results["sum_position_tables"] = position_sum
        results["all_players_count"] = all_players_count
        results["counts_match"] = (position_sum == 693 and all_players_count == 693)

        # Check indexes
        cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type = 'index'")
        results["indexes"] = cursor.fetchall()

        # Spot-check player
        cursor.execute(
            'SELECT "Player", "club", "Pos", "position_group", "Min", "90s", "low_sample" '
            'FROM "all_players" WHERE "Player" = ?',
            (spot_check_player,),
        )
        all_player_row = cursor.fetchone()

        cursor.execute(
            'SELECT "Player", "club", "Pos", "position_group", "Min", "90s", "low_sample", "Gls_per90" '
            'FROM "forwards" WHERE "Player" = ?',
            (spot_check_player,),
        )
        forward_player_row = cursor.fetchone()

        results["spot_check"] = {
            "player_name": spot_check_player,
            "in_all_players": all_player_row is not None,
            "in_forwards": forward_player_row is not None,
            "all_players_data": all_player_row,
            "forwards_data": forward_player_row,
            "mins_match": (
                all_player_row is not None
                and forward_player_row is not None
                and all_player_row[4] == forward_player_row[4]
            ),
        }

    return results


def print_summary_report(
    db_path: Path,
    verification: dict,
    tables: dict[str, pd.DataFrame],
) -> None:
    """
    Prints a formatted summary report covering file path, file size,
    table row counts, and spot-check results.
    """
    file_size_bytes = db_path.stat().st_size
    file_size_kb = file_size_bytes / 1024.0

    print("\n" + "=" * 70)
    print(" PREMIER LEAGUE 2025-26 SQLITE DATABASE INGESTION REPORT")
    print("=" * 70)

    print("\n🗄️  1. Database File Details:")
    print(f"   • Database path : {db_path.resolve()}")
    print(f"   • File size     : {file_size_kb:.1f} KB ({file_size_bytes:,} bytes)")

    print("\n📊 2. Table Row & Column Counts:")
    for table_name, count in verification["table_counts"].items():
        col_count = len(tables[table_name].columns)
        print(f"   • {table_name:15s} : {count:3d} rows, {col_count:2d} columns")

    print("\n🔗 3. Row Count Verification:")
    pos_sum = verification["sum_position_tables"]
    all_cnt = verification["all_players_count"]
    if verification["counts_match"]:
        print(f"   ✅ Sum of 4 position tables ({pos_sum}) == all_players ({all_cnt}) == 693.")
    else:
        print(f"   ❌ MISMATCH: Sum of 4 position tables ({pos_sum}) vs all_players ({all_cnt}).")

    print("\n⚡ 4. Database Indexes Created (Player & club):")
    for idx_name, tbl_name in verification["indexes"]:
        print(f"   • Index: {idx_name:28s} ON table: '{tbl_name}'")

    print(f"\n🔍 5. Spot-Check Verification ({verification['spot_check']['player_name']}):")
    sc = verification["spot_check"]
    if sc["in_all_players"] and sc["in_forwards"] and sc["mins_match"]:
        all_row = sc["all_players_data"]
        fw_row = sc["forwards_data"]
        print(f"   ✅ Player found in both 'forwards' and 'all_players':")
        print(f"      - all_players : Player='{all_row[0]}', Club='{all_row[1]}', Min={all_row[4]}, 90s={all_row[5]:.1f}, low_sample={bool(all_row[6])}")
        print(f"      - forwards    : Player='{fw_row[0]}', Club='{fw_row[1]}', Min={fw_row[4]}, Gls_per90={fw_row[7]:.3f}")
        print(f"      - Verification: Minutes match perfectly ({all_row[4]} == {fw_row[4]}).")
    else:
        print(f"   ❌ Spot check failed for '{sc['player_name']}':")
        print(f"      In all_players: {sc['in_all_players']}, In forwards: {sc['in_forwards']}, Mins match: {sc['mins_match']}")

    print("\n" + "=" * 70 + "\n")


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest player feature sheets into a SQLite database."
    )
    parser.add_argument(
        "--features-file",
        type=Path,
        default=FEATURES_FILE_DEFAULT,
        help="Path to features/player_features.xlsx (default: 'features/player_features.xlsx').",
    )
    parser.add_argument(
        "--db-file",
        type=Path,
        default=DATABASE_FILE_DEFAULT,
        help="Path to output sqlite database (default: 'data/pl_dashboard.db').",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    features_file: Path = args.features_file
    db_file: Path = args.db_file

    print(f"Starting SQLite database construction...")
    print(f"Source features file : {features_file.resolve()}")
    print(f"Target database file : {db_file.resolve()}")

    # 1. Load the 4 position-group sheets
    print("\nLoading position sheets from Excel...")
    sheets = load_feature_sheets(features_file)
    for name, df in sheets.items():
        print(f"  • Loaded sheet '{name}': {len(df)} rows, {len(df.columns)} columns")

    # 2. Build the combined 'all_players' table
    print("\nBuilding combined 'all_players' table...")
    all_players_df = build_all_players_table(sheets)
    print(f"  • Created 'all_players': {len(all_players_df)} rows, {len(all_players_df.columns)} columns")

    # Group all 5 tables together
    tables_to_write: dict[str, pd.DataFrame] = {
        **sheets,
        "all_players": all_players_df,
    }

    # 3. Write tables and create indexes in SQLite
    print(f"\nWriting 5 tables and building indexes in {db_file}...")
    save_tables_and_indexes(tables_to_write, db_file)
    print("Database write complete.")

    # 4. Verify database contents
    print("\nRunning verification pass on SQLite database...")
    verification = verify_database(db_file, spot_check_player="Erling Haaland")

    # 5. Print summary report
    print_summary_report(db_file, verification, tables_to_write)


if __name__ == "__main__":
    main()
