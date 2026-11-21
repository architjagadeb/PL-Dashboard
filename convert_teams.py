import os, glob, re
import pandas as pd
try:
    from ftfy import fix_text
except ImportError:
    fix_text = lambda s: s

BASE = "Teams"
OUT = "csv_export/teams"
INVIS = re.compile("[\u00ad\u200b\u200c\u200d\ufeff]")

def clean(v):
    if isinstance(v, str):
        return INVIS.sub("", fix_text(v))
    return v

def flatten(cols):
    out = []
    for c in cols:
        parts = [str(p) for p in c if not str(p).startswith("Unnamed")]
        out.append("_".join(parts).strip().lower().replace(" ", "_"))
    return out

for team_dir in sorted(glob.glob(f"{BASE}/*/")):
    team = os.path.basename(team_dir.rstrip("/"))
    folder = team.lower().replace(" ", "_")
    os.makedirs(f"{OUT}/{folder}", exist_ok=True)
    for xl in glob.glob(team_dir + "*.xlsx"):
        raw = pd.read_excel(xl, sheet_name=None, header=None)
        for sheet, df in raw.items():
            two_level = df.iloc[0].isna().sum() > len(df.columns) / 3
            if two_level:
                head = pd.MultiIndex.from_arrays([df.iloc[0].ffill(), df.iloc[1]])
                cols = flatten(head)
                body = df.iloc[2:]
            else:
                cols = [str(c) for c in df.iloc[0]]
                body = df.iloc[1:]
            body = body.copy()
            body.columns = cols
            body = body.map(clean).dropna(how="all")
            name = sheet.lower().replace(" ", "_")
            body.to_csv(f"{OUT}/{folder}/{name}.csv", index=False, encoding="utf-8-sig")
            print(team, sheet, body.shape)