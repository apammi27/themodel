# 8rain Station® Advantage Betting Model

An Elo-based daily predictive model for NBA, NFL, MLB, WNBA, and EPL that outputs predictions in the [8rain Station® CSV upload format](https://docs.google.com/spreadsheets/d/1M0qrS-c1azK2BQbEmjnqr-RXPFUpHN9fgltym9u18zI/edit?usp=sharing).

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env

# Run today's predictions (all sports)
python main.py run

# Run for a specific date
python main.py run --date 2025-04-15

# Run for specific sports
python main.py run --sports nba,mlb

# Preview output in terminal without writing files
python main.py run --print

# Test with built-in demo data (no network needed)
python main.py run --demo --sports nba,nfl,mlb,wnba,epl --print
```

Output CSVs are written to `./output/` by default, one file per sport:
```
output/
  nba_20250415.csv
  nfl_20250415.csv
  mlb_20250415.csv
  wnba_20250415.csv
  epl_20250415.csv
```

Upload any of these directly to the 8rain Station® **Weightings** page.

---

## How the Model Works

### Core: Elo Ratings

Every team has an Elo rating (starting at 1500). After each game the winner gains points, the loser loses them, proportional to how surprising the result was.

- **Win probability**: `P(home wins) = 1 / (1 + 10^((away_elo - (home_elo + home_advantage)) / 400))`
- **Home advantage**: applied as bonus Elo points (configurable per sport)
- **First run**: ratings are bootstrapped from ESPN standings (current season win %)
- **Persistence**: ratings are saved to `storage/ratings.json` and accumulate daily

### Spread & Total Predictions

| Market | Formula |
|---|---|
| Expected margin | `elo_diff / spread_divisor` (divisor calibrated per sport) |
| Spread probability | `1 - Normal.cdf((line - expected_margin) / margin_std)` |
| Expected total | blend of team offensive + defensive ratings |
| Total probability | `1 - Normal.cdf((line - expected_total) / total_std)` |

### Player Props (MLB)

MLB batter and pitcher props use:
1. **Rolling weighted average** (exponential decay, last 15 games)
2. **Poisson distribution** for discrete count stats (strikeouts, home runs)
3. **Normal distribution** for volume stats (hits, bases, runs)
4. Optional opponent adjustment

Pass player IDs on the command line to generate props:
```bash
python main.py run --sports mlb \
  --batters 592450,660271 \
  --pitchers 543037
```

> Player IDs are 6-digit MLB IDs from mlb.com URLs, e.g. `mlb.com/player/mike-trout-545361`.

### Data Sources

| League | Source | Auth |
|---|---|---|
| All schedules | ESPN Site API (unofficial) | None |
| Team standings/stats | ESPN Site API | None |
| MLB schedule + pitchers | MLB Stats API (official) | None |
| MLB player game logs | MLB Stats API | None |
| Live market odds | The Odds API (optional) | API key |

---

## Commands

```bash
# Generate predictions
python main.py run [--sports nba,nfl,mlb,wnba,epl] [--date YYYY-MM-DD] [--print] [--demo]

# Update Elo from yesterday's completed games
python main.py update-elo

# Show current Elo ratings table
python main.py ratings [--sports nba] [--top 10]

# Reset Elo bootstrapping (re-init from standings on next run)
python main.py reset [--sports nba]

# Apply end-of-season regression to mean
python main.py regress [--sports nba,nfl]
```

---

## Configuration

All settings live in `.env` (copy from `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `OUTPUT_DIR` | `./output` | Where CSV files are written |
| `CACHE_DIR` | `./.cache` | API response cache (hourly TTL) |
| `RATINGS_FILE` | `./storage/ratings.json` | Elo ratings persistence |
| `PROP_LOOKBACK` | `15` | Games to look back for player props |
| `ODDS_API_KEY` | *(optional)* | The Odds API key for live market lines |

League-level model parameters (K-factor, home advantage, spread divisor, std devs) are in `config.py`.

---

## Daily Workflow

```bash
# Morning: generate today's predictions
python main.py run

# Upload to 8rain Station:
#   → Weightings page → Upload CSV → select today's file

# Evening: ratings auto-update from completed games on next run
# (or manually trigger):
python main.py update-elo
```

---

## Output Format

Every game produces rows for:
- **Moneyline** (`head_to_head / h2h`): 2 rows, home + away
- **Spread** (`spread / spread`): 2 rows at model-implied line
- **Run line** (MLB only): 2 rows at ±1.5
- **Total** (`total / total`): 2 rows at model-implied total
- **Team runs/points** (`team_prop`): 2 rows per team
- **Player props** (MLB, when IDs supplied): 2 rows per prop per player

Probabilities are decimal (e.g. `0.5715` = 57.15%).

---

## Architecture

```
themodel/
├── main.py              CLI entry point
├── config.py            League configs, team code mappings, prop std devs
├── data/
│   ├── espn_client.py   ESPN Site API wrapper (schedules, standings, stats)
│   └── mlb_client.py    MLB Stats API wrapper (official, free)
├── models/
│   ├── elo.py           Elo engine (expected win prob, update, regression)
│   ├── game_model.py    Win prob → spread → total predictions
│   ├── prop_model.py    Player prop rolling averages + probability calc
│   ├── daily_runner.py  Main orchestrator (ties it all together)
│   └── demo_runner.py   Offline demo using hard-coded sample data
├── output/
│   └── formatter.py     8rain Station CSV serialiser
└── storage/
    └── ratings_store.py  Elo persistence (JSON)
```
