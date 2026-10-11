#!/usr/bin/env python3
"""
ingest_clubs.py - Step 1: Ingest and combine Premier League club workbooks.

Ingests Premier League 2025-26 player statistics from 20 club Excel workbooks
plus one league workbook (epl.xlsx), and combines them into 5 clean league-wide tables:
  1. standard
  2. goalkeeping
  3. shooting
  4. playing time
  5. miscellaneous

Scope:
  - Reads 20 club workbooks with 2-row headers.
  - Normalizes sheet names and club names based on epl.xlsx 'Overall'.
  - Validates standard sheet columns ('Ast' and 'Min').
  - Removes junk rows ('Total') and drops 'Matches' column.
  - Repairs CP1252/UTF-8 player name mojibake.
  - Saves 5 separate combined .xlsx tables and prints a summary report.
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import openpyxl
import pandas as pd


# 5 canonical sheet types expected across club workbooks
CANONICAL_SHEETS: list[str] = [
    "standard",
    "goalkeeping",
    "shooting",
    "playing time",
    "miscellaneous",
]

# Sheet name variations and common typos to canonical mapping
SHEET_NAME_ALIASES: dict[str, str] = {
    "standard": "standard",
    "goalkeeping": "goalkeeping",
    "goalkepping": "goalkeeping",      # tolerated misspelling
    "shooting": "shooting",
    "playing time": "playing time",
    "playingtime": "playing time",
    "miscellaneous": "miscellaneous",
    "miscellneous": "miscellaneous",    # tolerated misspelling
    "misc": "miscellaneous",
}

# Known club name overrides from filename stem to official name in epl.xlsx
CLUB_NAME_OVERRIDES: dict[str, str] = {
    "manchester united": "Manchester Utd",
    "man united": "Manchester Utd",
    "man utd": "Manchester Utd",
}

# Regex to identify typical CP1252/UTF-8 mojibake signatures or replacement chars
MOJIBAKE_PATTERN = re.compile(
    r"[\ufffd]|Ã[\x80-\xff\w]?|Å[\x80-\xff\w]?|Ä[\x80-\xff\w]?|Â[\x80-\xff\w]?|â€"
)


def normalize_sheet_name(raw_name: str) -> Optional[str]:
    """
    Normalizes a sheet name:
    - Strips leading/trailing spaces and collapses inner whitespace.
    - Converts to lowercase.
    - Handles case-insensitivity, extra spaces, and common misspellings.
    """
    if not raw_name or not isinstance(raw_name, str):
        return None
    cleaned = " ".join(raw_name.strip().lower().split())
    return SHEET_NAME_ALIASES.get(cleaned)


def find_workbook_sheets(file_path: Path) -> dict[str, str]:
    """
    Inspects workbook sheets and returns a mapping:
      canonical_sheet_type -> actual_sheet_name_in_file
    """
    wb = openpyxl.load_workbook(file_path, read_only=True)
    sheet_map: dict[str, str] = {}
    for actual_name in wb.sheetnames:
        canonical = normalize_sheet_name(actual_name)
        if canonical and canonical not in sheet_map:
            sheet_map[canonical] = actual_name
    wb.close()
    return sheet_map


def get_official_club_names(epl_path: Path) -> list[str]:
    """
    Reads the 'Overall' sheet from epl.xlsx and extracts the official club names.
    """
    if not epl_path.exists():
        raise FileNotFoundError(f"League workbook not found at: {epl_path}")

    wb = openpyxl.load_workbook(epl_path, read_only=True, data_only=True)
    if "Overall" not in wb.sheetnames:
        wb.close()
        raise ValueError(f"'Overall' sheet not found in {epl_path}. Sheets found: {wb.sheetnames}")

    ws = wb["Overall"]
    header = None
    squad_col_idx = 1
    official_names: list[str] = []

    for row_idx, row in enumerate(ws.iter_rows(values_only=True)):
        if row_idx == 0:
            header = [str(c).strip() if c is not None else "" for c in row]
            if "Squad" in header:
                squad_col_idx = header.index("Squad")
            continue

        if row and len(row) > squad_col_idx and row[squad_col_idx] is not None:
            squad_name = str(row[squad_col_idx]).strip()
            if squad_name and squad_name.lower() != "squad":
                official_names.append(squad_name)

    wb.close()
    return official_names


def map_club_filename_to_official(
    file_path: Path,
    official_names: list[str],
) -> str:
    """
    Maps a club file name to the official club name used in epl.xlsx's 'Overall' sheet.
    Replaces underscores with spaces, resolves aliases (e.g. Manchester United -> Manchester Utd),
    and validates against the official names list.
    """
    stem = file_path.stem
    # Replace underscores with spaces and collapse multiple spaces
    cleaned = " ".join(stem.replace("_", " ").strip().split())

    # Check known explicit overrides
    cleaned_lower = cleaned.lower()
    if cleaned_lower in CLUB_NAME_OVERRIDES:
        return CLUB_NAME_OVERRIDES[cleaned_lower]

    # Check direct case-insensitive match against official names
    for official in official_names:
        if cleaned_lower == official.lower():
            return official

    # Check prefix or partial match against official names (e.g. Nottingham -> Nottingham Forest)
    for official in official_names:
        if cleaned_lower.startswith(official.lower()) or official.lower().startswith(cleaned_lower):
            return official

    # Fallback to cleaned name if not found in official list
    return cleaned


def find_club_workbooks(clubs_dir: Path) -> list[Path]:
    """
    Discovers club Excel workbooks within clubs_dir.
    Supports:
      1. Flat directory containing *.xlsx (e.g. Teams/*.xlsx)
      2. Nested club subdirectories (e.g. Teams/Arsenal/Arsenal.xlsx)
    Ignores temporary Excel files (starting with '~$') and league workbook ('epl.xlsx').
    """
    if not clubs_dir.exists():
        raise FileNotFoundError(f"Clubs directory not found at: {clubs_dir}")

    # First check flat files in directory
    direct_files = [
        f for f in clubs_dir.glob("*.xlsx")
        if not f.name.startswith("~$") and f.name.lower() != "epl.xlsx"
    ]
    if direct_files:
        return sorted(direct_files)

    # Next check subdirectories
    nested_files = [
        f for f in clubs_dir.glob("*/*.xlsx")
        if not f.name.startswith("~$") and f.name.lower() != "epl.xlsx"
    ]
    if nested_files:
        return sorted(nested_files)

    return []


def fix_garbled_name(name: str) -> tuple[str, bool, bool]:
    """
    Fixes garbled player names caused by UTF-8 text opened as Windows-1252.

    For every player name, attempts: name.encode('cp1252').decode('utf-8').
    - If successful, doesn't contain replacement characters ('\\ufffd'), and is free
      of mojibake, the fixed string is returned (was_fixed = True).
    - If the name is already clean ASCII or valid Unicode, it is preserved.
    - If the name was garbled but decoding failed or left replacement characters,
      it is flagged as unresolved (is_unresolved = True).

    Returns:
        (resolved_name, was_fixed, is_unresolved)
    """
    if not isinstance(name, str) or not name.strip():
        return name, False, False

    has_replacement = "\ufffd" in name
    looked_garbled = has_replacement or bool(MOJIBAKE_PATTERN.search(name))

    try:
        candidate = name.encode("cp1252").decode("utf-8")
        if "\ufffd" not in candidate:
            if candidate != name:
                # Successfully converted mojibake
                if not MOJIBAKE_PATTERN.search(candidate):
                    return candidate, True, False
                else:
                    # Partially changed but still garbled
                    return name, False, True
            else:
                # Pure ASCII, identical result
                return name, False, False
        else:
            # Result contains replacement characters
            return name, False, True
    except (UnicodeEncodeError, UnicodeDecodeError):
        if looked_garbled:
            return name, False, True
        else:
            # Valid non-ASCII Unicode (e.g. 'Raúl Jiménez', 'Emiliano Martínez')
            return name, False, False


def clean_sheet_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans a single sheet DataFrame:
    - Drops 'Matches' column if present.
    - Removes junk rows where player name contains 'Total' (Squad Total, Opponent Total).
    """
    df_clean = df.copy()

    # Drop 'Matches' column if present
    if "Matches" in df_clean.columns:
        df_clean = df_clean.drop(columns=["Matches"])

    # Locate player column (typically 'Player')
    player_col = None
    for col in df_clean.columns:
        if str(col).strip().lower() == "player":
            player_col = col
            break

    if player_col is not None:
        # Filter out rows where player contains "Total" (case-insensitive)
        is_total = df_clean[player_col].astype(str).str.contains("Total", case=False, na=False)
        df_clean = df_clean[~is_total].copy()

    return df_clean


def validate_standard_sheet(df: pd.DataFrame, club_name: str, file_path: Path) -> bool:
    """
    Validates that a club's 'standard' sheet has 'Ast' and 'Min' columns.
    If missing, prints a clear warning and returns False so the club can be skipped.
    """
    has_ast = "Ast" in df.columns
    has_min = "Min" in df.columns
    if not (has_ast and has_min):
        missing = []
        if not has_ast:
            missing.append("'Ast'")
        if not has_min:
            missing.append("'Min'")
        print(
            f"⚠️  WARNING: Skipping club '{club_name}' ({file_path.name}) from standard table: "
            f"missing required column(s) {', '.join(missing)} (suspected shooting-table duplicate)."
        )
        return False
    return True


def apply_player_name_fixes(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[tuple[str, str]], set[str]]:
    """
    Applies fix_garbled_name across the Player column of a DataFrame.

    Returns:
        (updated_df, fixed_pairs, unresolved_names)
    """
    df_updated = df.copy()
    player_col = None
    for col in df_updated.columns:
        if str(col).strip().lower() == "player":
            player_col = col
            break

    fixed_pairs: list[tuple[str, str]] = []
    unresolved_names: set[str] = set()

    if player_col is None:
        return df_updated, fixed_pairs, unresolved_names

    cleaned_players = []
    for val in df_updated[player_col]:
        if pd.isna(val):
            cleaned_players.append(val)
            continue
        original_name = str(val).strip()
        fixed_name, was_fixed, is_unresolved = fix_garbled_name(original_name)
        if was_fixed:
            fixed_pairs.append((original_name, fixed_name))
            cleaned_players.append(fixed_name)
        else:
            if is_unresolved:
                unresolved_names.add(original_name)
            cleaned_players.append(original_name)

    df_updated[player_col] = cleaned_players
    return df_updated, fixed_pairs, unresolved_names


def combine_club_workbooks(
    club_files: list[Path],
    club_mapping: dict[Path, str],
) -> tuple[
    dict[str, pd.DataFrame],
    list[tuple[str, str]],
    list[str],
    list[tuple[str, str]],
    set[str],
]:
    """
    Loops through the 20 club workbooks for each of the 5 sheet types:
    - Reads sheets with 2nd row as column headers (header=1).
    - Checks required columns on standard sheets (Ast, Min).
    - Removes junk rows ('Total') and drops 'Matches'.
    - Adds 'club' column with official club name.
    - Repairs player name mojibake.
    - Stacks all clubs into combined tables.

    Returns:
        (combined_tables, missing_sheets, skipped_standard_clubs, fixed_names, unresolved_names)
    """
    combined_tables: dict[str, pd.DataFrame] = {}
    missing_sheets: list[tuple[str, str]] = []  # (club_name, sheet_type)
    skipped_standard_clubs: list[str] = []
    all_fixed_names: list[tuple[str, str]] = []
    all_unresolved_names: set[str] = set()

    # Pre-inspect all sheet names across workbooks
    file_sheet_maps: dict[Path, dict[str, str]] = {
        f: find_workbook_sheets(f) for f in club_files
    }

    for canonical_sheet in CANONICAL_SHEETS:
        sheet_dfs: list[pd.DataFrame] = []

        for file_path in club_files:
            club_official = club_mapping[file_path]
            sheet_map = file_sheet_maps[file_path]

            if canonical_sheet not in sheet_map:
                missing_sheets.append((club_official, canonical_sheet))
                continue

            actual_sheet_name = sheet_map[canonical_sheet]

            # Read with header=1 (second row as column names)
            df = pd.read_excel(file_path, sheet_name=actual_sheet_name, header=1)

            # Step 3: Check standard table specifically for 'Ast' and 'Min'
            if canonical_sheet == "standard":
                if not validate_standard_sheet(df, club_official, file_path):
                    if club_official not in skipped_standard_clubs:
                        skipped_standard_clubs.append(club_official)
                    continue

            # Step 4: Clean junk rows and Matches column
            df = clean_sheet_dataframe(df)

            # Step 5: Fix player name mojibake
            df, fixed_pairs, unresolved = apply_player_name_fixes(df)
            all_fixed_names.extend(fixed_pairs)
            all_unresolved_names.update(unresolved)

            # Step 2: Add 'club' column using mapped official name
            # Insert as the first column for clean readability
            df.insert(0, "club", club_official)

            sheet_dfs.append(df)

        if sheet_dfs:
            combined_df = pd.concat(sheet_dfs, ignore_index=True)
        else:
            combined_df = pd.DataFrame()

        combined_tables[canonical_sheet] = combined_df

    return (
        combined_tables,
        missing_sheets,
        skipped_standard_clubs,
        all_fixed_names,
        all_unresolved_names,
    )


def save_combined_tables(
    tables: dict[str, pd.DataFrame],
    output_dir: Path,
) -> dict[str, Path]:
    """
    Saves each combined table as a separate Excel file in output_dir:
    e.g. combined_standard.xlsx, combined_goalkeeping.xlsx, etc.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: dict[str, Path] = {}

    for sheet_name, df in tables.items():
        filename = f"combined_{sheet_name.replace(' ', '_')}.xlsx"
        out_path = output_dir / filename
        df.to_excel(out_path, index=False, engine="openpyxl")
        saved_paths[sheet_name] = out_path

    return saved_paths


def print_summary_report(
    combined_tables: dict[str, pd.DataFrame],
    missing_sheets: list[tuple[str, str]],
    skipped_standard_clubs: list[str],
    fixed_names: list[tuple[str, str]],
    unresolved_names: set[str],
    saved_paths: dict[str, Path],
) -> None:
    """
    Prints a clear, formatted summary report covering:
      1. Row count and column count for each of the 5 combined tables.
      2. Any club that was missing a sheet.
      3. Any club skipped from the standard table in Step 3.
      4. List of repaired player names.
      5. List of unresolved mojibake names from Step 5.
    """
    print("\n" + "=" * 65)
    print(" PREMIER LEAGUE 2025-26 DATA INGESTION SUMMARY REPORT")
    print("=" * 65)

    print("\n📊 1. Combined Table Row & Column Counts:")
    for sheet_name, df in combined_tables.items():
        saved_file = saved_paths.get(sheet_name, Path("")).name
        print(f"   • {sheet_name:15} : {len(df):4d} rows, {len(df.columns):2d} columns  ({saved_file})")

    print("\n📋 2. Missing Sheets Check:")
    if missing_sheets:
        for club, sheet in missing_sheets:
            print(f"   ⚠️  Club '{club}' was missing sheet: '{sheet}'")
    else:
        print("   ✅ None. All 20 clubs had all 5 expected sheets.")

    print("\n🛡️  3. Standard Table Validation (Ast & Min check):")
    if skipped_standard_clubs:
        for club in skipped_standard_clubs:
            print(f"   ⚠️  Club skipped: '{club}' (missing 'Ast' or 'Min')")
    else:
        print("   ✅ None skipped. All 20 clubs possessed valid 'Ast' and 'Min' columns.")

    print(f"\n✨ 4. Player Name Mojibake Repair (Fixed: {len(set(fixed_names))} unique names):")
    if fixed_names:
        for orig, fixed in sorted(set(fixed_names)):
            print(f"   • \"{orig}\"  ->  \"{fixed}\"")
    else:
        print("   • No mojibake names encountered.")

    print(f"\n❓ 5. Unresolved Mojibake Names ({len(unresolved_names)}):")
    if unresolved_names:
        for name in sorted(unresolved_names):
            print(f"   ⚠️  Unresolved: \"{name}\"")
    else:
        print("   ✅ None! All detected mojibake player names resolved cleanly.")

    print("\n" + "=" * 65 + "\n")


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Ingest Premier League club workbooks and generate 5 combined tables."
    )
    parser.add_argument(
        "--clubs-dir",
        type=Path,
        default=Path("Teams"),
        help="Path to directory containing club .xlsx files (default: 'Teams').",
    )
    parser.add_argument(
        "--epl-file",
        type=Path,
        default=None,
        help="Path to league workbook epl.xlsx (default: auto-detected in EPL/ or current dir).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("combined_tables"),
        help="Directory to save combined tables (default: 'combined_tables').",
    )
    return parser.parse_args()


def resolve_epl_path(epl_arg: Optional[Path]) -> Path:
    """Finds epl.xlsx if not explicitly specified."""
    if epl_arg and epl_arg.exists():
        return epl_arg
    candidates = [
        Path("EPL/epl.xlsx"),
        Path("epl.xlsx"),
        Path("EPL/EPL.xlsx"),
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        "Could not find league workbook 'epl.xlsx'. Please specify --epl-file."
    )


def main() -> None:
    args = parse_arguments()

    print(f"Starting PL workbook ingestion...")
    print(f"Clubs directory: {args.clubs_dir.resolve()}")

    epl_path = resolve_epl_path(args.epl_file)
    print(f"League workbook: {epl_path.resolve()}")

    # Step 1: Discover club files and official club names from epl.xlsx
    club_files = find_club_workbooks(args.clubs_dir)
    if not club_files:
        raise FileNotFoundError(f"No club .xlsx files found in {args.clubs_dir}")
    print(f"Found {len(club_files)} club workbook(s).")

    official_names = get_official_club_names(epl_path)
    print(f"Loaded {len(official_names)} official club names from {epl_path.name} ('Overall').")

    # Build mapping from club filename to official name
    club_mapping = {
        f: map_club_filename_to_official(f, official_names) for f in club_files
    }
    print("Club name mapping:")
    for f, official in club_mapping.items():
        print(f"  • {f.name} -> {official}")

    # Step 2-5: Read, validate, clean, fix names, and combine
    print("\nProcessing sheets and combining tables...")
    (
        combined_tables,
        missing_sheets,
        skipped_standard_clubs,
        fixed_names,
        unresolved_names,
    ) = combine_club_workbooks(club_files, club_mapping)

    # Step 6: Save combined tables
    print(f"\nSaving 5 combined tables to: {args.output_dir.resolve()}")
    saved_paths = save_combined_tables(combined_tables, args.output_dir)

    # Step 7: Print summary report
    print_summary_report(
        combined_tables,
        missing_sheets,
        skipped_standard_clubs,
        fixed_names,
        unresolved_names,
        saved_paths,
    )


if __name__ == "__main__":
    main()
