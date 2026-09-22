"""Build the Tableau .hyper extract from the cleaned CSV.

Tableau Public only accepts workbooks whose data is an extract, so the packaged
.twbx carries Data/extract.hyper rather than a live CSV connection.
"""
import csv
import datetime as dt
from pathlib import Path

from tableauhyperapi import (HyperProcess, Telemetry, Connection, CreateMode, NOT_NULLABLE,
                             TableDefinition, SqlType, Inserter, TableName, Nullability)

PROJ = Path(__file__).resolve().parent.parent
CSV_PATH = PROJ / "data/clean/tableau_cars_flat.csv"
HYPER = PROJ / "tableau/extract.hyper"

COLS = [  # (csv header, hyper type)
    ("Month", SqlType.date()),
    ("State", SqlType.text()),
    ("Maker (legal entity)", SqlType.text()),
    ("Powertrain", SqlType.text()),
    ("Registrations", SqlType.big_int()),
    ("Brand", SqlType.text()),
    ("Parent Group", SqlType.text()),
    ("Origin Country", SqlType.text()),
    ("Region", SqlType.text()),
    ("State Code", SqlType.text()),
    ("State or UT", SqlType.text()),
    ("Map Location", SqlType.text()),
    ("Month Name", SqlType.text()),
    ("Month Number", SqlType.big_int()),
    ("Quarter", SqlType.text()),
    ("Days Covered", SqlType.big_int()),
    ("Is Partial Month", SqlType.bool()),
    ("Is EV", SqlType.bool()),
]


def convert(value, sql_type):
    t = str(sql_type)
    if t.startswith("DATE"):
        return dt.date.fromisoformat(value[:10])
    if t.startswith("BIG"):
        return int(value)
    if t.startswith("BOOL"):
        return value.strip().lower() == "true"
    return value


def main():
    HYPER.unlink(missing_ok=True)
    table = TableDefinition(
        table_name=TableName("Extract", "Extract"),
        columns=[TableDefinition.Column(name, ty, Nullability.NULLABLE) for name, ty in COLS],
    )
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, str(HYPER), CreateMode.CREATE_AND_REPLACE) as conn:
            conn.catalog.create_schema("Extract")
            conn.catalog.create_table(table)
            with open(CSV_PATH) as fh:
                reader = csv.DictReader(fh)
                rows = [[convert(r[name], ty) for name, ty in COLS] for r in reader]
            with Inserter(conn, table) as ins:
                ins.add_rows(rows)
                ins.execute()
            n = conn.execute_scalar_query(f'SELECT COUNT(*) FROM {table.table_name}')
            total = conn.execute_scalar_query(
                f'SELECT SUM("Registrations") FROM {table.table_name}')
    print(f"wrote {HYPER} - {n:,} rows, {total:,} registrations")


if __name__ == "__main__":
    main()
