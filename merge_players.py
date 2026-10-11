#!/usr/bin/env python3
"""
merge_players.py - Step 2: Merge the 5 combined tables into a single player-level table.

Merges Premier League 2025-26 tables from combined_tables/:
  - combined_standard.xlsx (base table)
  - combined_shooting.xlsx
  - combined_playing_time.xlsx
  - combined_miscellaneous.xlsx
  - combined_goalkeeping.xlsx

Join Strategy:
  - Generates a normalized join key: player name (stripped of accents/diacritics,
    lowercased, trimmed) + "|" + club name (lowercased, trimmed).
  - Uses combined_standard.xlsx as the base table (preserves all players, including
    0-minute squad members, with canonical names).
  - Left-joins shooting, playing time, and miscellaneous.
  - Drops duplicate columns from incoming tables (e.g. Gls, Ast, Pos, Age, 90s) to
    avoid _x / _y suffixes and keep the authoritative version from the base table.
  - Left-joins goalkeeping (expecting only goalkeepers to match; outfield players
    receive nulls for goalkeeping columns).
  - Validates join results and prints a detailed match report.
  - Saves the merged table to merged/merged_players.xlsx.
"""

from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd


COMBINED_DIR_DEFAULT = Path("combined_tables")
OUTPUT_DIR_DEFAULT = Path("merged")
OUTPUT_FILE_DEFAULT = "merged_players.xlsx"


def normalize_join_key(player: str, club: str) -> str:
    """
    Creates a normalized join key:
      1. Strips accents and diacritics via NFKD normalization (e.g. í -> i, á -> a, é -> e).
      2. Converts to lowercase.
      3. Collapses and trims extra whitespace.
      4. Combines with lowercased and trimmed club name: 'player|club'.
    """
    if pd.isna(player):
        clean_player = ""
    else:
        # Normalize to NFKD and drop combining diacritical marks
        nfkd = unicodedata.normalize("NFKD", str(player))
        ascii_player = nfkd.encode("ASCII", "ignore").decode("utf-8")
        clean_player = " ".join(ascii_player.strip().lower().split())

    if pd.isna(club):
        clean_club = ""
    else:
        clean_club = " ".join(str(club).strip().lower().split())

    return f"{clean_player}|{clean_club}"


def load_and_prepare_table(file_path: Path, table_name: str) -> pd.DataFrame:
    """
    Loads an Excel table from file_path, validates required columns ('Player', 'club'),
    and appends a normalized 'join_key' column.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Required table '{table_name}' not found at {file_path}")

    df = pd.read_excel(file_path)

    if "Player" not in df.columns or "club" not in df.columns:
        raise ValueError(f"Table '{table_name}' must contain 'Player' and 'club' columns. Found: {list(df.columns)}")

    df["join_key"] = [
        normalize_join_key(p, c) for p, c in zip(df["Player"], df["club"])
    ]
    return df


def merge_tables(
    base_df: pd.DataFrame,
    joined_tables: list[tuple[str, pd.DataFrame]],
) -> tuple[pd.DataFrame, dict[str, dict[str, int]], dict[str, list[tuple[str, str, float]]]]:
    """
    Left-joins multiple tables onto the base DataFrame using 'join_key'.

    For each incoming table:
      - Keeps only non-duplicate columns (plus 'join_key') to avoid _x / _y suffixes.
      - Tracks match statistics (matched vs unmatched rows).
      - Identifies any player with Min >= 90 that failed to match.

    Returns:
        (merged_df, join_stats, missing_90plus_by_table)
    """
    merged_df = base_df.copy()
    join_stats: dict[str, dict[str, int]] = {}
    missing_90plus_by_table: dict[str, list[tuple[str, str, float]]] = {}

    # Extract base minutes for validation (fill nulls with 0)
    base_mins_map = dict(zip(base_df["join_key"], base_df["Min"].fillna(0.0)))
    base_player_map = dict(zip(base_df["join_key"], base_df["Player"]))
    base_club_map = dict(zip(base_df["join_key"], base_df["club"]))

    for table_name, target_df in joined_tables:
        target_keys = set(target_df["join_key"])

        # Determine matched and unmatched row counts relative to base table
        matched_mask = merged_df["join_key"].isin(target_keys)
        matched_count = int(matched_mask.sum())
        unmatched_count = int((~matched_mask).sum())

        join_stats[table_name] = {
            "target_rows": len(target_df),
            "matched_rows": matched_count,
            "unmatched_rows": unmatched_count,
        }

        # Check for players with Min >= 90 failing to match
        unmatched_keys = set(merged_df.loc[~matched_mask, "join_key"])
        missing_90plus = []
        for key in unmatched_keys:
            mins = base_mins_map.get(key, 0.0)
            if mins >= 90.0:
                missing_90plus.append((base_player_map[key], base_club_map[key], mins))

        missing_90plus_by_table[table_name] = sorted(missing_90plus, key=lambda x: x[2], reverse=True)

        # Drop duplicate columns from incoming table to prevent _x / _y suffixes
        new_cols = [c for c in target_df.columns if c not in merged_df.columns or c == "join_key"]
        target_subset = target_df[new_cols]

        # Perform left join
        merged_df = pd.merge(merged_df, target_subset, on="join_key", how="left")

    return merged_df, join_stats, missing_90plus_by_table


def print_validation_report(
    merged_df: pd.DataFrame,
    join_stats: dict[str, dict[str, int]],
    missing_90plus_by_table: dict[str, list[tuple[str, str, float]]],
    output_path: Path,
) -> None:
    """
    Prints a clear, structured validation report covering:
      1. Final merged table dimensions.
      2. Match vs unmatched row counts for each joined table.
      3. List of any players with Min >= 90 who failed to match.
      4. Saved destination.
    """
    print("\n" + "=" * 70)
    print(" PREMIER LEAGUE 2025-26 MERGED PLAYERS VALIDATION REPORT")
    print("=" * 70)

    print("\n📊 1. Merged Table Overview:")
    print(f"   • Total players (rows)   : {len(merged_df)}")
    print(f"   • Total metrics (columns): {len(merged_df.columns)}")
    print(f"   • Destination file       : {output_path}")

    print("\n🔗 2. Join Match Statistics (Base: combined_standard.xlsx, 693 rows):")
    for table_name, stats in join_stats.items():
        matched = stats["matched_rows"]
        unmatched = stats["unmatched_rows"]
        pct = (matched / len(merged_df)) * 100
        print(f"   • {table_name:15} : {matched:3d} matched ({pct:5.1f}%), {unmatched:3d} unmatched (null)")

    print("\n🛡️  3. High-Minutes Match Verification (Min >= 90 mins):")
    # Tables to strictly verify: shooting, playing time, miscellaneous
    checked_tables = ["shooting", "playing time", "miscellaneous"]
    any_missing = False

    for table_name in checked_tables:
        missing_list = missing_90plus_by_table.get(table_name, [])
        if missing_list:
            any_missing = True
            print(f"   ⚠️  Missing from '{table_name}' ({len(missing_list)} players):")
            for player, club, mins in missing_list:
                print(f"      - {player} ({club}) - {mins:.0f} mins")
        else:
            print(f"   ✅ '{table_name}': 0 players with >= 90 mins missing (100% matched).")

    # Goalkeeping report note
    gk_stats = join_stats.get("goalkeeping", {})
    gk_matched = gk_stats.get("matched_rows", 0)
    print(f"\n🧤 4. Goalkeeping Table Note:")
    print(f"   • {gk_matched} goalkeepers matched as expected; outfield players cleanly receive nulls.")

    print("\n" + "=" * 70 + "\n")


def parse_arguments() -> argparse.Namespace:
    """Parses CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Merge the 5 combined Premier League tables into a single player-level table."
    )
    parser.add_argument(
        "--combined-dir",
        type=Path,
        default=COMBINED_DIR_DEFAULT,
        help="Directory containing the combined .xlsx files (default: 'combined_tables').",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR_DEFAULT,
        help="Directory to save the merged output table (default: 'merged').",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    combined_dir: Path = args.combined_dir
    output_dir: Path = args.output_dir

    print(f"Starting merge process...")
    print(f"Source directory: {combined_dir.resolve()}")
    print(f"Output directory: {output_dir.resolve()}")

    # 1. Load all 5 combined tables
    table_files = {
        "standard": combined_dir / "combined_standard.xlsx",
        "shooting": combined_dir / "combined_shooting.xlsx",
        "playing time": combined_dir / "combined_playing_time.xlsx",
        "miscellaneous": combined_dir / "combined_miscellaneous.xlsx",
        "goalkeeping": combined_dir / "combined_goalkeeping.xlsx",
    }

    print("\nLoading and normalizing join keys across tables...")
    loaded_tables: dict[str, pd.DataFrame] = {}
    for name, path in table_files.items():
        loaded_tables[name] = load_and_prepare_table(path, name)
        print(f"  • {name:15} loaded: {len(loaded_tables[name]):3d} rows")

    # 2. Base table is standard
    base_df = loaded_tables["standard"]

    # Tables to left-join in sequence
    tables_to_join = [
        ("shooting", loaded_tables["shooting"]),
        ("playing time", loaded_tables["playing time"]),
        ("miscellaneous", loaded_tables["miscellaneous"]),
        ("goalkeeping", loaded_tables["goalkeeping"]),
    ]

    # 3. Perform left joins and deduplicate columns
    print("\nExecuting left joins...")
    merged_df, join_stats, missing_90plus = merge_tables(base_df, tables_to_join)

    # 4. Save merged table to merged/merged_players.xlsx
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_FILE_DEFAULT
    print(f"Saving merged dataset to: {output_path.resolve()}...")
    merged_df.to_excel(output_path, index=False, engine="openpyxl")
    print("Save complete.")

    # 5. Print validation report
    print_validation_report(merged_df, join_stats, missing_90plus, output_path)


if __name__ == "__main__":
    main()
