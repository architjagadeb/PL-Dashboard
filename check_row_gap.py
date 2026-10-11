#!/usr/bin/env python3
"""
check_row_gap.py - Diagnostic check script for row count discrepancies.

Compares combined_standard.xlsx against combined_shooting.xlsx and
combined_miscellaneous.xlsx to analyze why standard has 693 rows while
shooting and miscellaneous have 551 rows.

Steps performed:
1. Loads combined_standard.xlsx and target combined table.
2. Builds unique player keys: (Player, club).
3. Identifies players present in standard but missing in target table.
4. Evaluates minutes played (Min) from standard for each missing player.
5. Summarizes breakdown:
   - Total missing count
   - 0 minutes played (including unplayed/bench players with NaN minutes)
   - 1 to 89 minutes played
   - 90 or more minutes played
6. Lists all missing players with >= 90 minutes (name, club, minutes played).
"""

from pathlib import Path
import pandas as pd


COMBINED_DIR = Path("combined_tables")
STANDARD_FILE = COMBINED_DIR / "combined_standard.xlsx"
SHOOTING_FILE = COMBINED_DIR / "combined_shooting.xlsx"
MISC_FILE = COMBINED_DIR / "combined_miscellaneous.xlsx"


def analyze_missing_players(
    std_df: pd.DataFrame,
    target_df: pd.DataFrame,
    target_name: str,
) -> None:
    """
    Compares standard dataframe against target dataframe by (Player, club) key.
    Calculates minutes breakdown for missing players and prints formatted report.
    """
    # 1. Build unique player + club key
    # Use tuple or delimited string key
    std_df = std_df.copy()
    target_df = target_df.copy()

    std_df["player_club_key"] = std_df["Player"].astype(str).str.strip() + " || " + std_df["club"].astype(str).str.strip()
    target_df["player_club_key"] = target_df["Player"].astype(str).str.strip() + " || " + target_df["club"].astype(str).str.strip()

    target_keys = set(target_df["player_club_key"])

    # 2. Find players in standard but NOT in target table
    missing_mask = ~std_df["player_club_key"].isin(target_keys)
    missing_df = std_df[missing_mask].copy()

    # 3. Pull Min values (treat NaN/null as 0 minutes played)
    missing_df["Min_num"] = pd.to_numeric(missing_df["Min"], errors="coerce").fillna(0.0)

    total_missing = len(missing_df)
    zeros = (missing_df["Min_num"] == 0).sum()
    between_1_and_89 = ((missing_df["Min_num"] >= 1) & (missing_df["Min_num"] < 90)).sum()
    ninety_plus = (missing_df["Min_num"] >= 90).sum()

    ninety_plus_df = missing_df[missing_df["Min_num"] >= 90].sort_values(by="Min_num", ascending=False)

    # 4. Print formatted report
    print("=" * 70)
    print(f" REPORT: combined_standard.xlsx vs {target_name}")
    print("=" * 70)
    print(f"Standard table rows : {len(std_df)}")
    print(f"{target_name:19} : {len(target_df)}")
    print(f"Total missing in {target_name.split()[0]} : {total_missing}")
    print("-" * 70)
    print("Minutes Played (Min) Breakdown for Missing Players:")
    print(f"  • 0 minutes (bench / unused) : {zeros:3d}")
    print(f"  • 1 to 89 minutes            : {between_1_and_89:3d}")
    print(f"  • 90 or more minutes         : {ninety_plus:3d}")
    print("-" * 70)

    if ninety_plus > 0:
        print("Missing Players with 90+ Minutes (worth investigating):")
        for _, row in ninety_plus_df.iterrows():
            player = row["Player"]
            club = row["club"]
            mins = int(row["Min_num"]) if row["Min_num"].is_integer() else row["Min_num"]
            pos = row.get("Pos", "N/A")
            print(f"  • {player} ({club}) - {mins} mins [Pos: {pos}]")
    else:
        print("No missing players with >= 90 minutes.")
    print("=" * 70)
    print()


def main() -> None:
    if not STANDARD_FILE.exists():
        raise FileNotFoundError(f"Missing {STANDARD_FILE}. Please run ingest_clubs.py first.")
    if not SHOOTING_FILE.exists():
        raise FileNotFoundError(f"Missing {SHOOTING_FILE}.")
    if not MISC_FILE.exists():
        raise FileNotFoundError(f"Missing {MISC_FILE}.")

    # Load dataframes
    std_df = pd.read_excel(STANDARD_FILE)
    sht_df = pd.read_excel(SHOOTING_FILE)
    misc_df = pd.read_excel(MISC_FILE)

    # Run check for combined_shooting.xlsx
    analyze_missing_players(std_df, sht_df, "combined_shooting.xlsx")

    # Run check for combined_miscellaneous.xlsx
    analyze_missing_players(std_df, misc_df, "combined_miscellaneous.xlsx")


if __name__ == "__main__":
    main()
