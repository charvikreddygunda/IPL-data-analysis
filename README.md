# The Auction Room 🏏

**Learn data science by doing an IPL analyst's job, on real ball-by-ball data.**

It's a mega-auction year, and you've just been hired as the data analyst for an IPL franchise. The Director of Cricket wants evidence, not opinions. Your mentor, Meera, won't hand you answers; she'll show you how to find them. You start from raw deliveries and finish with a retention decision, a squad plan, a live auction and a simulated season.

The whole game is one HTML file. There's nothing to install: open `index.html` in a browser.

## How to play

| # | Chapter | What you do | Data science idea |
|---|---|---|---|
| 0 | Briefing | Pick one of the 10 franchises and read the Director's brief | Defining the objective |
| 1 | Raw data | Read real overs ball by ball, decide what counts as a ball faced and whose wicket it is, then group 44,000 deliveries into one row per player and calculate strike rate, average and economy | Data cleaning, group-by aggregation, rates vs totals, missing values |
| 2 | Explore | Sort, spot a small-sample trap, adjust for sample size, filter a shortlist | Sorting, sample size, shrinkage, boolean filters |
| 3 | Same ruler | Settle "Russell's strike rate or Narine's economy?" with steps from average, then weight your own Impact Score | Mean, standard deviation, z-scores, weighted scores |
| 4 | Fit | Read your home ground, then pick between a famous name and a better fit | Feature engineering, context |
| 5 | Retentions | Keep up to 5 of your current squad at fixed slabs (₹18/14/11/18/14 Cr), or let them go to auction | Expected value vs fixed cost |
| 6 | Squad plan | Lay out your playing XI and 4 backups; empty slots become the shopping list | Constraints, planning |
| 7 | War board | Choose targets and set a maximum bid for each | Valuation, budget allocation |
| 8 | Auction night | A live auction against 9 rivals, with a 12-second clock, jump bids, an earpiece and a pushy Director; then an accelerated round | Decisions under uncertainty, the winner's curse |
| 9 | Season | Each team picks its best XI for every ground; 2,000 simulated seasons; then your report card | Monte Carlo simulation |

Switch between **Beginner** and **Coder (pandas)** modes at any time. Coder mode shows the Python behind every step.

## Repo layout

```
index.html                         the game (self-contained HTML, CSS and JS, with the player data embedded)
data/players.csv                   one row per active player (built from the ball-by-ball data)
data/players.json                  the same rows, embedded into index.html
data/sample_overs.json             the real overs used in chapter 1
data/teams.csv                     franchises, home grounds and ground profiles
scripts/build_players.py           ball-by-ball CSV → players.csv / players.json / sample_overs.json
scripts/embed.py                   writes the JSON into index.html
notebooks/analyst_notebook.ipynb   the same analysis in pandas, chapter by chapter
```

## Run it

- **Play locally:** open `index.html` in any modern browser.
- **GitHub Pages:** go to *Settings → Pages → Deploy from a branch → `main` / root*. The game will be live at `https://<your-username>.github.io/<repo-name>/`.
- **Notebook:** put `ball_by_ball_data.csv` in `data/`, run `pip install pandas numpy matplotlib jupyter`, then run `jupyter notebook notebooks/analyst_notebook.ipynb`.

### Rebuild the data (e.g. after a new season)

```bash
python scripts/build_players.py data/ball_by_ball_data.csv
python scripts/embed.py
```

`ball_by_ball_data.csv` is about 44 MB. GitHub accepts it (the limit is 100 MB per file), or you can keep it out of the repo and add it to `.gitignore`.

## Game rules and model

- **Scouting window:** the IPL 2024, 2025 and 2026 seasons (2026 is partial in this dataset). Active players have played in 2025 or 2026 with at least 120 balls faced or 180 bowled. That gives 154 players.
- **Current squads:** each player's most recent team.
- **Hand-labelled:** nationality (overseas) and wicketkeepers aren't in the data, so they're labelled in `build_players.py`.
- **Impact score:** z-scores of average, strike rate, wickets per match, economy and death-overs economy, all shrunk for small samples. The weights are yours to choose.
- **Market price:** calibrated so the whole pool is worth about 85% of the money in the room, with a soft ceiling near ₹32 Cr.
- **Your value:** the market price, adjusted for ground fit (using real strike rates against spin and pace) and for whether the player fills an empty slot in your plan (+35% for an XI slot, +10% for a backup).
- **Purse and retentions:** these follow the 2025 mega-auction rules (₹120 Cr; slabs of ₹18, 14, 11, 18 and 14 Cr). Squads are capped at 15 players (max 6 overseas, 4 in the XI) to keep the game short.
- **Ground profiles:** simplified assumptions. The dataset has no venue column.

## Roadmap ideas

- [ ] Multiplayer auction rooms with friends
- [ ] Powerplay and middle-overs splits; a venue-level dataset to measure grounds instead of assuming them
- [ ] Back-test the price model against real auction prices
- [ ] Right to Match (RTM) cards
- [ ] Save progress between sessions

## Disclaimer

This is an unofficial, fan-made educational project. It is not affiliated with the IPL, the BCCI or any franchise. Team names and colours are used for reference only, and no official logos are included. Vikram and Meera are fictional characters.
