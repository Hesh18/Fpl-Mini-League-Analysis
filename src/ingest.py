"""Download raw daily snapshots from the Fantasy Premier League API."""

import gzip
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE_URL = "https://fantasy.premierleague.com/api/"
HEADERS = {"User-Agent": "fpl-mini-league-analytics (personal project)"}
LEAGUE_ID = 548302
DEFAULT_RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR = Path(os.environ.get("FPL_RAW_DIR", DEFAULT_RAW_DIR))

MAX_ATTEMPTS = 3
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MIN_PLAYERS = 500


def fetch_json(endpoint):
    """Call one FPL API endpoint and return the decoded JSON, retrying brief failures."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(BASE_URL + endpoint, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            status = getattr(error.response, "status_code", None)
            retryable = status is None or status in RETRYABLE_STATUS
            if not retryable or attempt == MAX_ATTEMPTS:
                raise
            wait = 2 ** attempt
            print(f"Attempt {attempt} for {endpoint} failed ({error}); retrying in {wait}s")
            time.sleep(wait)


def save_raw(data, folder, filename):
    """Save data as a gzip-compressed JSON file under RAW_DIR/<folder>/<filename>."""
    path = RAW_DIR / folder / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    with gzip.open(temp_path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    temp_path.replace(path)
    print(f"Saved {path}")
    return path


def snapshot_bootstrap(today):
    """Save today's full game state: every player, team and gameweek."""
    data = fetch_json("bootstrap-static/")
    players = len(data.get("elements", []))
    if players < MIN_PLAYERS:
        raise RuntimeError(f"Bootstrap has only {players} players; refusing to save it.")
    save_raw(data, "bootstrap", f"{today}.json.gz")
    return data


def remove_personal_names(league_data):
    """Drop managers' real names; keep their IDs and team names."""
    for row in league_data["standings"]["results"]:
        row.pop("player_name", None)
    league_data.pop("new_entries", None)


def snapshot_league(league_id, today):
    """Save the league table and return the manager IDs in it."""
    data = fetch_json(f"leagues-classic/{league_id}/standings/")
    remove_personal_names(data)
    save_raw(data, "league", f"{league_id}_{today}.json.gz")

    standings = data["standings"]
    if standings["has_next"]:
        raise RuntimeError("League has more than 50 managers; add paging.")

    manager_ids = [row["entry"] for row in standings["results"]]
    if not manager_ids:
        raise RuntimeError(f"No managers found in league {league_id}.")
    return manager_ids


def snapshot_manager_histories(manager_ids, today):
    """Save each manager's gameweek history and return the gameweeks each one played."""
    played = {}
    for manager_id in manager_ids:
        data = fetch_json(f"entry/{manager_id}/history/")
        save_raw(data, "manager_history", f"{manager_id}_{today}.json.gz")
        played[manager_id] = [row["event"] for row in data["current"]]
        time.sleep(1)
    return played


def final_gameweeks(bootstrap):
    """Return the gameweeks whose points FPL has marked as final."""
    return [
        event["id"]
        for event in bootstrap["events"]
        if event["finished"] and event["data_checked"]
    ]


def save_gameweek_points(gameweek):
    """Save every player's points for one final gameweek. Returns False if we already have it."""
    filename = f"{gameweek}.json.gz"
    if (RAW_DIR / "gameweek_live" / filename).exists():
        return False
    data = fetch_json(f"event/{gameweek}/live/")
    players = len(data.get("elements", []))
    if players < MIN_PLAYERS:
        raise RuntimeError(f"Gameweek {gameweek} has only {players} players; refusing to save it.")
    save_raw(data, "gameweek_live", filename)
    return True


def save_manager_picks(manager_id, gameweek):
    """Save one manager's 15 picks for one final gameweek. Returns False if we already have it."""
    filename = f"{manager_id}_{gameweek}.json.gz"
    if (RAW_DIR / "manager_picks" / filename).exists():
        return False
    data = fetch_json(f"entry/{manager_id}/event/{gameweek}/picks/")
    if len(data.get("picks", [])) != 15:
        raise RuntimeError(f"Manager {manager_id} gameweek {gameweek} doesn't have 15 picks; refusing to save it.")
    save_raw(data, "manager_picks", filename)
    return True


def backfill_final_gameweeks(bootstrap, played):
    """Download picks and player points for final gameweeks we don't have yet."""
    final = set(final_gameweeks(bootstrap))
    downloaded = 0

    for gameweek in sorted(final):
        if save_gameweek_points(gameweek):
            downloaded += 1
            time.sleep(1)

    for manager_id, gameweeks in played.items():
        for gameweek in gameweeks:
            if gameweek in final and save_manager_picks(manager_id, gameweek):
                downloaded += 1
                time.sleep(1)

    print(f"Final gameweeks: {len(final)}. New files downloaded: {downloaded}")


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"Snapshot date (UTC): {today}")
    failures = 0
    bootstrap = None
    played = None

    try:
        bootstrap = snapshot_bootstrap(today)
    except Exception:
        failures += 1
        print("FAILED: bootstrap")
        traceback.print_exc()

    try:
        manager_ids = snapshot_league(LEAGUE_ID, today)
        print(f"Found {len(manager_ids)} managers")
        played = snapshot_manager_histories(manager_ids, today)
    except Exception:
        failures += 1
        print("FAILED: league or manager histories")
        traceback.print_exc()

    if bootstrap is None or played is None:
        print("SKIPPED: picks and player points (they need both parts above)")
    else:
        try:
            backfill_final_gameweeks(bootstrap, played)
        except Exception:
            failures += 1
            print("FAILED: picks or player points")
            traceback.print_exc()

    if failures:
        sys.exit(f"{failures} part(s) failed. Saved what succeeded.")
    print("Done.")


if __name__ == "__main__":
    main()