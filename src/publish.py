"""Export the tested mart tables as Parquet files for the app to read."""

import os
from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_DIR / "data" / "warehouse.duckdb"
DEFAULT_PUBLISH_DIR = PROJECT_DIR / "data" / "published"
PUBLISH_DIR = Path(os.environ.get("FPL_PUBLISH_DIR", DEFAULT_PUBLISH_DIR))


def main():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    marts = [
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE starts_with(table_name, 'mart_') ORDER BY table_name"
        ).fetchall()
    ]
    if not marts:
        raise SystemExit("No mart tables found. Run dbt build first.")

    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
    for table in marts:
        path = PUBLISH_DIR / f"{table}.parquet"
        con.execute(f"COPY {table} TO '{path.as_posix()}' (FORMAT parquet)")
        rows = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"Published {table}: {rows} rows to {path}")
    con.close()


if __name__ == "__main__":
    main()