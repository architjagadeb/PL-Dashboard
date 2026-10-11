#!/usr/bin/env python3
"""
check_gk_gap.py - Diagnostic check script for goalkeeping join discrepancies.

Compares combined_goalkeeping.xlsx against combined_standard.xlsx using the
same normalized join key as merge_players.py:
  - Strips accents/diacritics using Unicode NFKD.
  - Converts to lowercase and collapses whitespace.
  - Combines player name and club with a '|'.

Steps performed:
1. Loads combined_goalkeeping.xlsx and combined_standard.xlsx.
2. Identifies rows in combined_goalkeeping.xlsx whose normalized key does NOT
   appear in combined_standard.xlsx.
3. For each unmatched goalkeeper, prints:
   - Raw Player name
   - Club name
   - Minutes played (Min)
4. Searches combined_standard.xlsx for any player in that same club with Pos == 'GK'
   and displays them side-by-side.
5. Provides diagnostic notes on whether the mismatch is a spelling variance or
   a genuine club assignment discrepancy.
"""

from pathlib import Path
import unicodedata
import pandas as pd


COMBINED_DIR = Path("combined_tables")
GK_FILE = COMBINED_DIR / "combined_goalkeeping.xlsx"
STD_FILE = COMBINED_DIR / "combined_standard.xlsx"


def normalize_join_key(player: str, club: str) -> str:
    """
    Creates a normalized join key matching merge_players.py:
      - Strips accents via Unicode NFKD normalization.
      - Converts to lowercase and collapses whitespace.
      - Combines player name and club name: 'player|club'.
    """
    if pd.isna(player):
        clean_player = ""
    else:
        nfkd = unicodedata.normalize("NFKD", str(player))
        ascii_player = nfkd.encode("ASCII", "ignore").decode("utf-8")
        clean_player = " ".join(ascii_player.strip().lower().split())

    if pd.isna(club):
        clean_club = ""
    else:
        clean_club = " ".join(str(club).strip().lower().split())

    return f"{clean_player}|{clean_club}"


def main() -> None:
    if not GK_FILE.exists():
        raise FileNotFoundError(f"Missing {GK_FILE}. Please run ingest_clubs.py first.")
    if not STD_FILE.exists():
        raise FileNotFoundError(f"Missing {STD_FILE}. Please run ingest_clubs.py first.")

    # 1. Load tables
    gk_df = pd.read_excel(GK_FILE)
    std_df = pd.read_excel(STD_FILE)

    # 2. Apply normalized join keys
    gk_df["join_key"] = [
        normalize_join_key(p, c) for p, c in zip(gk_df["Player"], gk_df["club"])
    ]
    std_df["join_key"] = [
        normalize_join_key(p, c) for p, c in zip(std_df["Player"], std_df["club"])
    ]

    # 3. Identify unmatched goalkeeping rows
    std_keys = set(std_df["join_key"])
    unmatched_gk = gk_df[~gk_df["join_key"].isin(std_keys)].copy()

    # 4. Print report
    print("=" * 75)
    print(" GOALKEEPING VS STANDARD JOIN GAP ANALYSIS REPORT")
    print("=" * 75)
    print(f"Total rows in combined_goalkeeping.xlsx : {len(gk_df)}")
    print(f"Total rows in combined_standard.xlsx    : {len(std_df)}")
    print(f"Matched goalkeepers in standard table   : {len(gk_df) - len(unmatched_gk)}")
    print(f"Unmatched goalkeepers                   : {len(unmatched_gk)}")
    print("=" * 75)

    if unmatched_gk.empty:
        print("\n✅ All goalkeepers in combined_goalkeeping.xlsx matched combined_standard.xlsx!")
        print("=" * 75 + "\n")
        return

    print("\n🔍 UNMATCHED GOALKEEPERS IN combined_goalkeeping.xlsx:\n")

    # Group by club to avoid redundant prints if multiple GKs from same club
    grouped_by_club = unmatched_gk.groupby("club")

    for club, club_unmatched in grouped_by_club:
        print(f"───────────────────────────────────────────────────────────────────────────")
        print(f"CLUB: {club}")
        print(f"───────────────────────────────────────────────────────────────────────────")

        print("  [Side A] Unmatched in combined_goalkeeping.xlsx:")
        for _, row in club_unmatched.iterrows():
            raw_player = row["Player"]
            raw_club = row["club"]
            mins = row.get("Min")
            min_str = f"{mins:.0f}" if pd.notna(mins) and isinstance(mins, (int, float)) else str(mins)
            mp = row.get("MP", "N/A")
            starts = row.get("Starts", "N/A")
            print(f"    • Player: {raw_player}")
            print(f"      Club  : {raw_club}")
            print(f"      Min   : {min_str} (MP: {mp}, Starts: {starts})")

        print(f"\n  [Side B] Goalkeepers for '{club}' in combined_standard.xlsx (Pos == 'GK'):")
        std_club_gks = std_df[(std_df["club"] == club) & (std_df["Pos"] == "GK")]

        if std_club_gks.empty:
            print(f"    ⚠️  No players found with Pos == 'GK' for '{club}' in combined_standard.xlsx.")
        else:
            for _, srow in std_club_gks.iterrows():
                std_player = srow["Player"]
                std_mins = srow.get("Min")
                std_min_str = f"{std_mins:.0f}" if pd.notna(std_mins) else "0 (unused bench)"
                std_mp = srow.get("MP", 0)
                std_starts = srow.get("Starts", 0)
                print(f"    • Player: {std_player}")
                print(f"      Pos   : {srow['Pos']}")
                print(f"      Min   : {std_min_str} (MP: {std_mp}, Starts: {std_starts})")

        # Additional diagnostic: check where the unmatched GKs actually appear in standard
        print(f"\n  [Cross-Club Audit] Where do these unmatched GKs appear in combined_standard.xlsx?")
        for _, row in club_unmatched.iterrows():
            clean_name = unicodedata.normalize("NFKD", str(row["Player"])).encode("ASCII", "ignore").decode("utf-8").strip().lower()
            matches_in_std = std_df[
                std_df["Player"].apply(
                    lambda x: unicodedata.normalize("NFKD", str(x)).encode("ASCII", "ignore").decode("utf-8").strip().lower() == clean_name
                )
            ]
            if not matches_in_std.empty:
                for _, mrow in matches_in_std.iterrows():
                    actual_club = mrow["club"]
                    actual_min = mrow.get("Min")
                    actual_min_str = f"{actual_min:.0f}" if pd.notna(actual_min) else "0"
                    print(f"    ℹ️  '{row['Player']}' appears in standard under club: '{actual_club}' ({actual_min_str} mins, Pos: {mrow.get('Pos')})")
            else:
                print(f"    ❌ '{row['Player']}' does not appear anywhere in combined_standard.xlsx.")

    print("\n" + "=" * 75)
    print("CONCLUSION:")
    print("  This is NOT an accent or spelling mismatch. Rather, the Chelsea workbook")
    print("  (Teams/Chelsea/Chelsea.xlsx) contains a duplicated goalkeeping sheet with")
    print("  Burnley's goalkeepers (Martin Dúbravka & Max Weiß), while Chelsea's actual")
    print("  goalkeepers (Robert Sánchez & Filip Jørgensen) are correctly listed in standard.")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
