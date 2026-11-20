"""FPL mini-league dashboard, built on the tested tables the daily pipeline publishes."""

import os

import pandas as pd
import streamlit as st

DATA_BASE = os.environ.get(
    "FPL_DATA_BASE",
    "https://raw.githubusercontent.com/Hesh18/Fpl-Mini-League-Analysis/data/published",
)
REPO_URL = "https://github.com/Hesh18/Fpl-Mini-League-Analysis"
CHIP_NAMES = {"3xc": "Triple captain", "bboost": "Bench boost", "freehit": "Free hit", "wildcard": "Wildcard"}

st.set_page_config(page_title="FPL Mini-League", page_icon="⚽", layout="wide")


@st.cache_data(ttl=3600)
def load_table(name):
    """Download one published table. Cached for an hour."""
    return pd.read_parquet(f"{DATA_BASE}/{name}.parquet")


try:
    summary = load_table("mart_league_summary").sort_values("league_rank")
    captain = load_table("mart_captain_decisions")
    top_half = load_table("mart_top_half_weeks")
    players = load_table("mart_player_consistency")
except Exception:
    st.error("Couldn't load the league data right now. Try again in a few minutes.")
    st.stop()

as_of = summary["as_of_date"].iloc[0]
gameweek = summary["latest_gameweek"].iloc[0]
gameweek_final = bool(summary["latest_gameweek_final"].iloc[0])

st.title("FPL Mini-League")
if gameweek_final:
    st.caption(f"Through gameweek {gameweek} · data as of {as_of:%d %b %Y} · updates daily")
else:
    st.caption(f"Gameweek {gameweek} in progress, points so far · data as of {as_of:%d %b %Y} · updates daily")

league_tab, captain_tab, top_half_tab, players_tab = st.tabs(["League", "Captaincy", "Top half", "Players"])

with league_tab:
    leader = summary.iloc[0]
    runner_up = summary.iloc[1]
    most_bench = summary.loc[summary["bench_points"].idxmax()]
    most_hits = summary.loc[summary["hit_points"].idxmax()]
    no_transfers = summary.loc[summary["transfers_made"] == 0, "team_name"].tolist()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Title race",
        f"{runner_up['points_behind_leader']} pts",
        delta=f"{leader['team_name']} lead {runner_up['team_name']}",
        delta_color="off",
        delta_arrow="off",
        help="The gap between first and second place.",
        border=True,
    )
    col2.metric(
        "Most points left on the bench",
        f"{most_bench['bench_points']} pts",
        delta=most_bench["team_name"],
        delta_color="off",
        delta_arrow="off",
        help="Points scored by players on the bench, all season. Auto-subs already count, so these points were truly wasted.",
        border=True,
    )
    col3.metric(
        "Most points spent on hits",
        f"{most_hits['hit_points']} pts",
        delta=most_hits["team_name"] if most_hits["hit_points"] > 0 else "Nobody yet",
        delta_color="off",
        delta_arrow="off",
        help="Points deducted for transfers beyond the free ones.",
        border=True,
    )
    col4.metric(
        "No transfers all season",
        f"{len(no_transfers)} teams",
        delta=", ".join(no_transfers) if no_transfers else "Everyone has made one",
        delta_color="off",
        delta_arrow="off",
        help="Teams that haven't made a single transfer since joining.",
        border=True,
    )

    st.subheader("League table")
    st.dataframe(
        summary,
        hide_index=True,
        width="stretch",
        height="content",
        column_order=[
            "league_rank",
            "team_name",
            "total_points",
            "points_behind_leader",
            "bench_points",
            "bench_points_per_gameweek",
            "hit_points",
            "transfers_made",
            "first_gameweek",
        ],
        column_config={
            "league_rank": st.column_config.NumberColumn("Rank"),
            "team_name": st.column_config.TextColumn("Team"),
            "total_points": st.column_config.NumberColumn("Points"),
            "points_behind_leader": st.column_config.NumberColumn("Behind 1st"),
            "bench_points": st.column_config.NumberColumn("Bench pts"),
            "bench_points_per_gameweek": st.column_config.NumberColumn("Bench pts / GW", format="%.1f"),
            "hit_points": st.column_config.NumberColumn("Hit pts"),
            "transfers_made": st.column_config.NumberColumn("Transfers"),
            "first_gameweek": st.column_config.NumberColumn("Joined GW"),
        },
    )

    st.subheader("Bench points per gameweek")
    st.caption("Per gameweek, so managers who joined late are compared fairly.")
    st.bar_chart(
        summary,
        x="team_name",
        y="bench_points_per_gameweek",
        x_label="",
        y_label="Bench points per gameweek",
        horizontal=True,
        sort="-bench_points_per_gameweek",
    )

with captain_tab:
    last_final = captain["gameweek"].max()
    st.caption(f"Finished gameweeks only: 1 to {last_final}. Points lost = your best starter minus your captain.")
    if not gameweek_final:
        st.info(f"Gameweek {gameweek} is still being played. It appears here once FPL confirms the final points.")

    captain["best_pick"] = captain["captain_points_lost"] == 0
    captain["beat_crowd"] = captain["captain_points"] > captain["crowd_captain_points"]
    captain["behind_crowd"] = captain["captain_points"] < captain["crowd_captain_points"]

    by_team = (
        captain.groupby("team_name")
        .agg(
            gameweeks=("gameweek", "count"),
            points_lost=("captain_points_lost", "sum"),
            best_pick_weeks=("best_pick", "sum"),
            beat_crowd_weeks=("beat_crowd", "sum"),
            behind_crowd_weeks=("behind_crowd", "sum"),
            captain_changes=("changed_captain", "sum"),
        )
        .reset_index()
    )
    by_team["lost_per_gameweek"] = (by_team["points_lost"] / by_team["gameweeks"]).round(1)
    by_team = by_team.sort_values("lost_per_gameweek", ascending=False)

    most_lost = by_team.iloc[0]
    least_lost = by_team.iloc[-1]
    favourites = captain["picked_captain_name"].value_counts()
    most_changes = by_team["captain_changes"].max()
    changers = by_team.loc[by_team["captain_changes"] == most_changes, "team_name"].tolist()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Most points lost to captain picks",
        f"{most_lost['lost_per_gameweek']} pts / GW",
        delta=most_lost["team_name"],
        delta_color="off",
        delta_arrow="off",
        help="Average points lost per gameweek by not captaining the best starter.",
        border=True,
    )
    col2.metric(
        "Sharpest captain picker",
        f"{least_lost['lost_per_gameweek']} pts / GW",
        delta=least_lost["team_name"],
        delta_color="off",
        delta_arrow="off",
        help="The lowest average points lost per gameweek.",
        border=True,
    )
    col3.metric(
        "League's favourite captain",
        favourites.index[0],
        delta=f"{favourites.iloc[0]} of {len(captain)} picks",
        delta_color="off",
        delta_arrow="off",
        help="The player our league has captained most often.",
        border=True,
    )
    col4.metric(
        "Most captain changes",
        f"{most_changes} changes",
        delta=", ".join(changers),
        delta_color="off",
        delta_arrow="off",
        help="How many times a team switched captain from one gameweek to the next.",
        border=True,
    )

    st.subheader("Captain table")
    st.caption(
        "The crowd's captain is the player most FPL managers worldwide captained that week. "
        "You beat the crowd when your captain outscored him."
    )
    st.dataframe(
        by_team,
        hide_index=True,
        width="stretch",
        height="content",
        column_order=[
            "team_name",
            "gameweeks",
            "points_lost",
            "lost_per_gameweek",
            "best_pick_weeks",
            "beat_crowd_weeks",
            "behind_crowd_weeks",
            "captain_changes",
        ],
        column_config={
            "team_name": st.column_config.TextColumn("Team"),
            "gameweeks": st.column_config.NumberColumn("GWs"),
            "points_lost": st.column_config.NumberColumn("Pts lost"),
            "lost_per_gameweek": st.column_config.NumberColumn("Lost / GW", format="%.1f"),
            "best_pick_weeks": st.column_config.NumberColumn("Best-pick weeks"),
            "beat_crowd_weeks": st.column_config.NumberColumn("Beat the crowd"),
            "behind_crowd_weeks": st.column_config.NumberColumn("Behind the crowd"),
            "captain_changes": st.column_config.NumberColumn("Captain changes"),
        },
    )

    st.subheader("Points lost per gameweek")
    st.caption("Per gameweek, so managers who joined late are compared fairly.")
    st.bar_chart(
        by_team,
        x="team_name",
        y="lost_per_gameweek",
        x_label="",
        y_label="Points lost per gameweek",
        horizontal=True,
        sort="-lost_per_gameweek",
    )

    st.subheader("Who the league captains")
    top_captains = favourites.head(5).rename_axis("player").reset_index(name="times")
    top_captains["share"] = (100 * top_captains["times"] / len(captain)).round(0)
    st.dataframe(
        top_captains,
        hide_index=True,
        column_config={
            "player": st.column_config.TextColumn("Player"),
            "times": st.column_config.NumberColumn("Times captained"),
            "share": st.column_config.NumberColumn("Share of picks", format="%d%%"),
        },
    )

    st.subheader("One team, week by week")
    team = st.selectbox("Team", summary["team_name"].tolist())
    weeks = captain.loc[captain["team_name"] == team].sort_values("gameweek").copy()
    weeks["chip"] = weeks["chip"].map(CHIP_NAMES).fillna("")
    weeks["captain"] = weeks["picked_captain_name"].where(
        ~weeks["vice_captain_stepped_in"],
        weeks["picked_captain_name"] + " → " + weeks["captain_name"] + " (vice)",
    )
    st.dataframe(
        weeks,
        hide_index=True,
        width="stretch",
        height="content",
        column_order=[
            "gameweek",
            "chip",
            "captain",
            "captain_points",
            "best_option_name",
            "best_option_points",
            "captain_points_lost",
            "crowd_captain_name",
            "crowd_captain_points",
        ],
        column_config={
            "gameweek": st.column_config.NumberColumn("GW"),
            "chip": st.column_config.TextColumn("Chip"),
            "captain": st.column_config.TextColumn("Captain"),
            "captain_points": st.column_config.NumberColumn("Captain pts"),
            "best_option_name": st.column_config.TextColumn("Best starter"),
            "best_option_points": st.column_config.NumberColumn("Best pts"),
            "captain_points_lost": st.column_config.NumberColumn("Pts lost"),
            "crowd_captain_name": st.column_config.TextColumn("Crowd's captain"),
            "crowd_captain_points": st.column_config.NumberColumn("Crowd pts"),
        },
    )

with top_half_tab:
    st.caption(
        f"Finished gameweeks only: 1 to {captain['gameweek'].max()}. "
        "A top-half week means you outscored more than half of the league that week, after transfer hits."
    )
    if not gameweek_final:
        st.info(f"Gameweek {gameweek} is still being played. It appears here once FPL confirms the final points.")

    top_half = top_half.sort_values(["top_half_share", "longest_run"], ascending=False)
    top_half["record"] = top_half["top_half_weeks"].astype(str) + " of " + top_half["gameweeks_played"].astype(str)
    top_half["share_pct"] = (100 * top_half["top_half_share"]).round(0)

    st.dataframe(
        top_half,
        hide_index=True,
        width="stretch",
        height="content",
        column_order=["team_name", "record", "share_pct", "longest_run", "current_run"],
        column_config={
            "team_name": st.column_config.TextColumn("Team"),
            "record": st.column_config.TextColumn("Top-half weeks"),
            "share_pct": st.column_config.NumberColumn("Share", format="%d%%"),
            "longest_run": st.column_config.NumberColumn("Longest run"),
            "current_run": st.column_config.NumberColumn("Current run"),
        },
    )
    st.caption(
        "Counted out of the weeks each manager has played, so late joiners aren't marked down. "
        "A run is top-half weeks in a row; the current run is the one still going."
    )

with players_tab:
    st.caption(
        f"Finished gameweeks only: 1 to {captain['gameweek'].max()}. "
        "A good game means a player scored more than the middle score of everyone in his position who played 60+ minutes that week."
    )
    POSITIONS = {"Goalkeepers": "GKP", "Defenders": "DEF", "Midfielders": "MID", "Forwards": "FWD"}
    position_name = st.radio("Position", list(POSITIONS), index=2, horizontal=True)
    in_position = players["position"] == POSITIONS[position_name]

    shown = players.loc[in_position & players["is_ranked"]].copy()
    shown = shown.sort_values(["good_game_share", "full_games"], ascending=False)
    shown["record"] = shown["good_games"].astype(str) + " of " + shown["full_games"].astype(str)
    shown["share_pct"] = (100 * shown["good_game_share"]).round(0)

    st.dataframe(
        shown,
        hide_index=True,
        width="stretch",
        height=420,
        column_order=["player_name", "team_name", "price_m", "record", "share_pct", "best_game"],
        column_config={
            "player_name": st.column_config.TextColumn("Player"),
            "team_name": st.column_config.TextColumn("Team"),
            "price_m": st.column_config.NumberColumn("Price", format="£%.1fm"),
            "record": st.column_config.TextColumn("Good games"),
            "share_pct": st.column_config.NumberColumn("Share", format="%d%%"),
            "best_game": st.column_config.NumberColumn("Best game"),
        },
    )
    left_out = int((in_position & ~players["is_ranked"]).sum())
    st.caption(
        f"Only players with 60+ minutes in at least 40% of finished gameweeks are ranked; "
        f"{left_out} {position_name.lower()} haven't played enough yet. "
        "Best game is his highest single score: steady players suit transfers, big hauls suit the captaincy."
    )

st.divider()
st.caption(
    f"Data is downloaded from the FPL API every day, checked by automated tests, "
    f"and only published here when every test passes. [How it works]({REPO_URL})"
)