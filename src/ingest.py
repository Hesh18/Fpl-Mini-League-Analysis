import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://fantasy.premierleague.com/api/"
HEADERS = {"User-Agent": "fpl-mini-league-analytics (personal project)"}
LEAGUE_ID = 548302
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def fetch_json(endpoint):
    """Call one FPL API endpoint and return the decoded JSON."""
    response = requests.get(BASE_URL + endpoint, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def save_raw(data, folder, filename):
    """Save data as a JSON file under data/raw/<folder>/<filename>."""
    path = RAW_DIR / folder / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"Saved {path}")
    return path


def snapshot_bootstrap(today):
    """Save today's full game state: every player, team and gameweek."""
    data = fetch_json("bootstrap-static/")
    save_raw(data, "bootstrap", f"{today}.json")
    return data


def snapshot_league(league_id, today):
    """Save the league table and return the manager IDs in it."""
    data = fetch_json(f"leagues-classic/{league_id}/standings/")
    save_raw(data, "league", f"{league_id}_{today}.json")

    standings = data["standings"]
    if standings["has_next"]:
        raise RuntimeError("League has more than 50 managers; add paging.")

    manager_ids = [row["entry"] for row in standings["results"]]
    if not manager_ids:
        raise RuntimeError(f"No managers found in league {league_id}.")
    return manager_ids


def snapshot_manager_histories(manager_ids, today):
    """Save each manager's gameweek-by-gameweek history."""
    for manager_id in manager_ids:
        data = fetch_json(f"entry/{manager_id}/history/")
        save_raw(data, "manager_history", f"{manager_id}_{today}.json")
        time.sleep(1)


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Snapshot date (UTC): {today}")

    snapshot_bootstrap(today)
    manager_ids = snapshot_league(LEAGUE_ID, today)
    print(f"Found {len(manager_ids)} managers")
    snapshot_manager_histories(manager_ids, today)
    print("Done.")


if __name__ == "__main__":
    main()