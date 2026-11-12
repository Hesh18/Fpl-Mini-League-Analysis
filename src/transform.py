"""Build the local DuckDB warehouse from raw snapshots and run data tests."""

import sys
from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "snapshots" / "raw"
DB_PATH = PROJECT_DIR / "data" / "warehouse.duckdb"
MODELS_DIR = PROJECT_DIR / "sql" / "models"
TESTS_DIR = PROJECT_DIR / "sql" / "tests"


def render(sql_path):
    """Read a SQL file and fill in the location of the raw data."""
    sql = sql_path.read_text(encoding="utf-8")
    return sql.replace("{{ raw_dir }}", RAW_DIR.as_posix())


def build_models(con):
    """Create one table per file in sql/models/, named after the file."""
    for sql_path in sorted(MODELS_DIR.glob("*.sql")):
        table = sql_path.stem
        con.execute(f"CREATE OR REPLACE TABLE {table} AS {render(sql_path)}")
        rows = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"Built {table}: {rows} rows")


def run_tests(con):
    """Run every test in sql/tests/. A test fails if it returns any rows."""
    failures = 0
    for sql_path in sorted(TESTS_DIR.glob("*.sql")):
        bad_rows = con.execute(render(sql_path)).fetchall()
        if bad_rows:
            failures += 1
            print(f"FAIL {sql_path.stem}: {len(bad_rows)} bad rows, first: {bad_rows[:3]}")
        else:
            print(f"PASS {sql_path.stem}")
    return failures


def main():
    if not RAW_DIR.exists():
        sys.exit(f"No raw data at {RAW_DIR}. Pull the data branch first.")

    con = duckdb.connect(str(DB_PATH))
    build_models(con)
    failures = run_tests(con)
    con.close()

    if failures:
        sys.exit(f"{failures} test(s) failed.")
    print("All tests passed.")


if __name__ == "__main__":
    main()