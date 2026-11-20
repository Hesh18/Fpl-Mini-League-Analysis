# FPL Mini-League Analytics

![Daily snapshot](https://github.com/Hesh18/Fpl-Mini-League-Analysis/actions/workflows/daily-snapshot.yml/badge.svg)

An automated, tested data pipeline that snapshots the Fantasy Premier League API every day and turns it into a league dashboard for a 15-person mini-league: who loses the most points on the bench, who takes the most transfer hits, whose captain picks cost them the most, and how far each manager is from first place. Runs entirely on free infrastructure.

**Example finding (through gameweek 10):** Number One sits 26 points off first place but has lost 73 points to captain picks, 34 more than the league's best captain picker (39).

**Live app:** https://fpl-mini-league-hesham.streamlit.app/

## What the app shows

**League tab:** the table, the title race, and who leaves the most points on the bench.

![The League tab](docs/app.png)

**Captaincy tab:** how many points each manager lost by captaining the wrong player, and who the league captains most.

![The Captaincy tab](docs/captaincy.png)

## Why I built this

I love Fantasy Premier League. My friends and I have played every season since 2015/16, and I finished in the top 1% in 2024/25. We've always relied on third-party apps, so I decided to build our own. I wanted to learn how to connect to APIs, run an automated pipeline on free infrastructure, and connect several tools into one pipeline and an app that’s both useful and fun for my league.

## How it works

```mermaid
flowchart LR
    API["FPL API<br/>undocumented, public"] -->|daily, GitHub Actions| ING["ingest.py<br/>retries, guards,<br/>strips real names"]
    ING --> RAW[("data branch<br/>raw snapshots, gzip JSON")]
    RAW --> STG["dbt staging<br/>7 models"]
    STG -->|52 tests gate every step| MART["dbt marts<br/>league summary,<br/>captain decisions,<br/>top-half weeks"]
    MART -->|only if all tests pass| PUB[("data branch<br/>published Parquet")]
    PUB --> APP["Streamlit app<br/>live"]
```

1. **Ingest:** every day a GitHub Actions workflow calls the FPL API, retries brief failures, refuses obviously broken responses, removes managers' real names, and saves gzip-compressed JSON to a separate `data` branch.
2. **Transform and test:** `dbt build` cleans the raw JSON into staging tables and two marts, running 52 data tests. A failing test stops everything downstream of it.
3. **Publish:** only when every test passes, the marts are exported as Parquet for the app. Raw data is always kept, so a bad day can be investigated and replayed.

![dbt lineage graph](docs/lineage.png)

## Data quality

| Test | Protects against |
| --- | --- |
| `assert_manager_points_reconcile` | A manager's season total not matching the sum of their gameweeks minus transfer hits |
| `assert_league_matches_history` | The league table disagreeing with managers' own histories |
| `assert_picks_reconcile_to_fpl` | A manager's picks not adding up to the gameweek score FPL reports |
| `assert_picks_complete` | A manager's gameweek missing from the picks, which would flatter their totals |
| `assert_picks_shape` | A squad that isn't 15 players, 11 starters and one captain |
| `assert_final_gameweeks_loaded` | FPL marking a gameweek final while its player points were never downloaded |
| `assert_top_half_matches_head_to_head` | A manager's top-half weeks disagreeing with a separate count of the weeks they outscored more than half the league |
| `assert_top_half_runs_valid` | Counts that contradict each other, like a longest run longer than all top-half weeks |
| `assert_players_present` | An empty or broken snapshot saved as a normal day |
| `assert_player_count_stable` | More than 5% of players appearing or disappearing overnight |
| `assert_snapshots_fresh` | Data silently ceasing to arrive |
| `assert_prices_in_range`, `assert_ownership_valid` | Unit and type errors (prices in tenths, numbers stored as text) |
| Built-in `unique`, `not_null`, `accepted_values`, `relationships` | Duplicates, blanks, unknown codes, broken links between tables |
| Model contracts on all three marts | The app's input changing column names or types |

## Design decisions

### 1. Raw data lives on a separate branch
GitHub wipes the runner after every run, so the daily files needed a permanent home that cost nothing. Committing them to `main` would have buried my own commits under a daily bot commit, and cloud storage meant setting up an account and credentials for a few megabytes. So they live on an orphan branch called `data` that shares no history with `main`: it's free, needs no secrets, and any past day can be recovered from Git history.

### 2. Every file is gzip-compressed
Each day's player file is about 2 MB and I keep all of them, which would add up to roughly 370 MB by May. Gzip makes each file about 11 times smaller, around 35 MB for the whole season, because JSON repeats the same field names hundreds of times. The file inside is still exactly what the API sent, and DuckDB reads gzip directly.

### 3. Real names are removed before anything is saved
The league endpoint returns managers' real full names, and I noticed my public repo was saving them every day without anyone's consent. I changed the ingest script to drop them before writing to disk, then force-pushed the data branch to remove the snapshot that already had them. Even then, GitHub can keep a force-pushed commit reachable by its link for a while, which taught me the real lesson: removing personal data afterwards is never complete, so don't store it in the first place. The analysis only needs manager IDs and team names anyway.

### 4. Raw data is always kept; only tested data is published
Each day's prices only exist on that day, so I never want to lose real data, but I also never want my friends to see wrong numbers. The pipeline retries temporary errors, refuses responses that clearly aren't data (fewer than 500 players), and saves whatever succeeded even if part of the run fails. Raw files are committed even on a failed run, but the file the app reads only updates after every dbt test passes. On a bad day, the run goes red, I get an email, and the app keeps showing yesterday's correct numbers.

### 5. dbt Core 1.12 instead of dbt v2
dbt v2 came out in September 2026, but its own docs warn it may not handle models that read local JSON files with `read_json()`, which is exactly what mine do, and its DuckDB support is still catching up. For a job that runs unattended every day, I chose the stable version: dbt Core 1.12 works with DuckDB, my JSON sources and Python 3.14.

### 6. Captain picks are judged against the players the manager actually started

FPL's data shows each team after automatic substitutions, so a bench player who came on looks like a starter. If I compared the captain with the best player in that final eleven, I'd sometimes blame a manager for not captaining someone they had left on the bench. So the model rebuilds the eleven each manager picked before the deadline and compares the captain only with those players. It changed 3 of 145 captain picks, 11 points in total. In gameweek 5, Pascal Gross came off H-Awy FC's bench and scored 14, more than
the captain. So the simple method said 8 points were lost when the real answer is 0. The number is still hindsight: nobody knows who will score most before the games, so it shows how a pick turned out, not whether it was a bad decision.

## What's next
- A test that fails if a real name ever appears in a raw league file
- A quarantine folder for raw files that fail tests, so one bad day doesn't keep the pipeline red until I step in
- Incremental dbt models once the season's data gets large
- Moving to dbt v2 once it fully supports local file sources

## Run it locally

```powershell
git clone https://github.com/Hesh18/Fpl-Mini-League-Analysis.git
cd Fpl-Mini-League-Analysis
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
git clone --branch data --single-branch https://github.com/Hesh18/Fpl-Mini-League-Analysis.git data\snapshots
cd dbt
dbt build
cd ..
streamlit run app/streamlit_app.py
```

## Stack

Python 3.14 · requests · pandas · DuckDB · dbt Core 1.12 with dbt-duckdb · GitHub Actions · Parquet · Streamlit

