"""FPL mini-league dashboard, built on the tested summary the daily pipeline publishes."""

import os

import pandas as pd
import streamlit as st

DATA_URL = os.environ.get(
    "FPL_DATA_URL",
    "https://raw.githubusercontent.com/Hesh18/Fpl-Mini-League-Analysis/data/published/mart_league_summary.parquet",
)
REPO_URL = "https://github.com/Hesh18/Fpl-Mini-League-Analysis"

st.set_page_config(page_title="FPL Mini-League", page_icon="⚽", layout="wide")


@st.cache_data(ttl=3600)
def load_summary(url):
    """Download the published league summary. Cached for an hour."""
    return pd.read_parquet(url)


try:
    summary = load_summary(DATA_URL).sort_values("league_rank")
except Exception:
    st.error("Couldn't load the league data right now. Try again in a few minutes.")
    st.stop()

as_of = summary["as_of_date"].iloc[0]
gameweek = summary["latest_gameweek"].iloc[0]

st.title("FPL Mini-League")
st.caption(f"Through gameweek {gameweek} · data as of {as_of:%d %b %Y} · updates daily")

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

st.divider()
st.caption(
    f"Data is downloaded from the FPL API every day, checked by automated tests, "
    f"and only published here when every test passes. [How it works]({REPO_URL})"
)