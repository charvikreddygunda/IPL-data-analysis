"""Build the game's player sheet from IPL ball-by-ball data.

Usage:
    python scripts/build_players.py data/ball_by_ball_data.csv

Writes:
    data/players.csv      one row per active player (the scout sheet)
    data/players.json     the same rows, embedded into index.html by scripts/embed.py
    data/sample_overs.json three real overs shown in chapter 1 of the game
"""
import json
import sys
from pathlib import Path

import pandas as pd

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "data/ball_by_ball_data.csv")
OUT = Path(__file__).resolve().parent.parent / "data"

RECENT = [2024, 2025, 2026]          # the scouting window
ACTIVE = [2025, 2026]                # must have played in one of these seasons
MIN_BALLS_FACED, MIN_BALLS_BOWLED = 120, 180

TEAM_IDS = {1: "RCB", 2: "SRH", 3: "MI", 6: "KKR", 129: "CSK", 134: "RR",
            252: "DC", 494: "PBKS", 614: "LSG", 615: "GT"}

# Not in the data: nationality and wicketkeeping role are labelled by hand.
OVERSEAS = {
    "A Nortje", "AD Russell", "AK Markram", "Azmatullah Omarzai", "C Connolly", "C Green",
    "D Brevis", "D Ferreira", "DA Miller", "E Malinga", "F du Plessis", "G Coetzee",
    "H Klaasen", "J Fraser-McGurk", "JC Archer", "JC Buttler", "JM Bairstow", "JP Inglis",
    "JR Hazlewood", "K Rabada", "L Ngidi", "LH Ferguson", "LS Livingstone", "M Jansen",
    "M Pathirana", "M Theekshana", "MA Starc", "MJ Santner", "MP Stoinis", "MR Marsh",
    "Mustafizur Rahman", "N Burger", "N Pooran", "N Thushara", "Noor Ahmad", "P Nissanka",
    "PD Salt", "PJ Cummins", "PWH de Silva", "Q de Kock", "R Powell", "R Ravindra",
    "R Shepherd", "RD Rickelton", "Rashid Khan", "SE Rutherford", "SM Curran", "SO Hetmyer",
    "SP Narine", "T Stubbs", "TA Boult", "TH David", "TM Head", "WG Jacks", "XC Bartlett",
}
KEEPERS = {
    "RR Pant", "SV Samson", "MS Dhoni", "JM Sharma", "RD Rickelton", "N Pooran", "Ishan Kishan",
    "Q de Kock", "H Klaasen", "KL Rahul", "JC Buttler", "P Simran Singh", "JP Inglis",
    "Dhruv Jurel", "PD Salt", "Abishek Porel", "JM Bairstow",
}
SPIN_WORDS = ("Offbreak", "Legbreak", "Orthodox", "Wrist spin", "Googly")
BOWLER_WICKETS = {"caught", "bowled", "lbw", "caught and bowled", "stumped", "hit wicket"}

d = pd.read_csv(SRC)
d = d[~d.is_super_over]
d["legal_bat"] = ~d.is_wide_ball                       # a wide is not a ball faced
d["legal_bowl"] = ~d.is_wide_ball & ~d.is_no_ball      # an over has 6 of these
d["conceded"] = d.batter_runs + d.wide_ball_runs + d.no_ball_runs   # byes & leg byes aren't the bowler's fault
d["bowler_wkt"] = d.is_wicket & d.wicket_kind.isin(BOWLER_WICKETS)
d["spin_ball"] = d.bowler_type.fillna("").str.contains("|".join(SPIN_WORDS))
d["death"] = d.over_number >= 15                        # overs 16-20

r = d[d.season_id.isin(RECENT)]

# --- appearances (batting, bowling or at the non-striker's end)
app = pd.concat([d[["match_id", "season_id", c]].rename(columns={c: "name"})
                 for c in ("batter", "bowler", "non_striker")]).drop_duplicates()
matches_recent = app[app.season_id.isin(RECENT)].groupby("name").match_id.nunique()
matches_career = app.groupby("name").match_id.nunique()

# --- current team = the team they last played for
side = pd.concat([
    d[["match_id", "season_id", "batter", "team_batting"]].set_axis(["m", "s", "name", "team"], axis=1),
    d[["match_id", "season_id", "non_striker", "team_batting"]].set_axis(["m", "s", "name", "team"], axis=1),
    d[["match_id", "season_id", "bowler", "team_bowling"]].set_axis(["m", "s", "name", "team"], axis=1),
])
current_team = side.sort_values(["s", "m"]).groupby("name").team.last().map(TEAM_IDS)

# --- batting (recent window)
bat = r.groupby("batter").agg(runs=("batter_runs", "sum"), balls=("legal_bat", "sum"))
outs = r[r.player_out.notna() & (r.wicket_kind != "retired hurt")].groupby("player_out").size()
bat["outs"] = outs.reindex(bat.index).fillna(0).astype(int)
vs = r[r.legal_bat].groupby(["batter", "spin_ball"]).agg(rr=("batter_runs", "sum"), bb=("batter_runs", "size"))
for flag, lab in ((True, "spin"), (False, "pace")):
    part = vs.xs(flag, level="spin_ball")
    bat[f"runs_vs_{lab}"] = part.rr.reindex(bat.index).fillna(0).astype(int)
    bat[f"balls_vs_{lab}"] = part.bb.reindex(bat.index).fillna(0).astype(int)

# --- bowling (recent window)
bowl = r.groupby("bowler").agg(balls_bowled=("legal_bowl", "sum"), runs_conceded=("conceded", "sum"),
                               wickets=("bowler_wkt", "sum"))
death = r[r.death].groupby("bowler").agg(death_balls=("legal_bowl", "sum"), death_runs=("conceded", "sum"))
bowl = bowl.join(death).fillna(0)
btype = d.groupby("bowler").bowler_type.agg(lambda s: s.mode().iat[0] if s.notna().any() else "")
bowl["bowling_type"] = ["S" if any(w in btype.get(n, "") for w in SPIN_WORDS) else "P" for n in bowl.index]

# --- the active pool
active = set(app[app.season_id.isin(ACTIVE)].name)
names = sorted(n for n in active
               if bat.balls.get(n, 0) >= MIN_BALLS_FACED or bowl.balls_bowled.get(n, 0) >= MIN_BALLS_BOWLED)

rows = []
for n in names:
    m = int(matches_recent.get(n, 0))
    b = bat.loc[n] if n in bat.index and bat.balls[n] >= 30 else None
    w = bowl.loc[n] if n in bowl.index and bowl.balls_bowled[n] >= 60 else None
    bowls_much = w is not None and w.balls_bowled >= 120 and w.balls_bowled / max(m, 1) >= 6   # an over a game
    bats_much = b is not None and b.balls >= MIN_BALLS_FACED and b.balls / max(m, 1) >= 5
    role = "WK" if n in KEEPERS else "AR" if bowls_much and bats_much else "BOWL" if bowls_much else "BAT"
    if role == "BOWL":
        b = None            # we don't scout specialist bowlers' batting
    rows.append({
        "name": n, "team": current_team.get(n, ""), "role": role, "overseas": int(n in OVERSEAS),
        "bowling_type": w.bowling_type if w is not None and bowls_much else "",
        "matches": m, "career_matches": int(matches_career.get(n, 0)),
        "runs": int(b.runs) if b is not None else None, "balls": int(b.balls) if b is not None else None,
        "outs": int(b.outs) if b is not None else None,
        "runs_vs_spin": int(b.runs_vs_spin) if b is not None else None, "balls_vs_spin": int(b.balls_vs_spin) if b is not None else None,
        "runs_vs_pace": int(b.runs_vs_pace) if b is not None else None, "balls_vs_pace": int(b.balls_vs_pace) if b is not None else None,
        "balls_bowled": int(w.balls_bowled) if w is not None and bowls_much else None,
        "runs_conceded": int(w.runs_conceded) if w is not None and bowls_much else None,
        "wickets": int(w.wickets) if w is not None and bowls_much else None,
        "death_balls": int(w.death_balls) if w is not None and bowls_much else None,
        "death_runs": int(w.death_runs) if w is not None and bowls_much else None,
    })
players = pd.DataFrame(rows)
OUT.mkdir(exist_ok=True)
players.to_csv(OUT / "players.csv", index=False)
(OUT / "players.json").write_text(json.dumps([{k: v for k, v in r.items() if v is not None and v == v} for r in rows], separators=(",", ":")))

# --- three real overs for the chapter-1 lesson: one with a wide, a bye/leg bye and a wicket
cand = r.groupby(["match_id", "innings", "over_number"]).agg(
    w=("is_wide_ball", "any"), lb=("is_leg_bye", "any"), wk=("bowler_wkt", "any"), ro=("wicket_kind", lambda s: (s == "run out").any()),
    bw=("bowler", "first"))
pick = cand[cand.w & cand.lb & cand.wk & cand.bw.isin(set(players[players.role != "BAT"].name))].head(1).index.tolist()
pick += cand[cand.ro & cand.bw.isin(set(players.name))].head(1).index.tolist()
overs = []
for mid, inn, ov in pick:
    o = r[(r.match_id == mid) & (r.innings == inn) & (r.over_number == ov)]
    overs.append({"season": int(o.season_id.iat[0]), "over": int(ov) + 1, "bowler": o.bowler.iat[0],
                  "balls": [{"batter": x.batter, "runs": int(x.batter_runs), "extras": int(x.extras),
                             "kind": "wide" if x.is_wide_ball else "no ball" if x.is_no_ball else "leg bye" if x.is_leg_bye else "bye" if x.is_bye else "",
                             "out": x.wicket_kind if isinstance(x.wicket_kind, str) else ""} for x in o.itertuples()]})
(OUT / "sample_overs.json").write_text(json.dumps(overs, separators=(",", ":")))
print(f"{len(players)} players · roles {players.role.value_counts().to_dict()} · "
      f"overseas {players.overseas.sum()} · teams {players.team.value_counts().to_dict()}")
