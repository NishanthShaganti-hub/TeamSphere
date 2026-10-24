"""Copy an existing SQLite TeamSphere database into an empty PostgreSQL database."""

import argparse
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, insert, inspect, select, text

from app import create_app
from extensions import db


def migrate(source_path: Path) -> dict[str, int]:
    """Copy shared tables from SQLite to the configured PostgreSQL database."""
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {source_path}")

    app = create_app()
    target_url = app.config["SQLALCHEMY_DATABASE_URI"]
    if not target_url.startswith("postgresql+"):
        raise ValueError("The configured target DATABASE_URL must use PostgreSQL.")

    source_engine = create_engine(f"sqlite:///{source_path.resolve()}")
    target_engine = create_engine(target_url)
    source_table_names = set(inspect(source_engine).get_table_names())
    model_tables = db.metadata.sorted_tables
    expected_tables = {table.name for table in model_tables}
    missing = expected_tables - source_table_names
    if missing:
        raise ValueError(
            "The SQLite database is missing expected TeamSphere tables: "
            + ", ".join(sorted(missing))
        )

    db.metadata.create_all(target_engine)
    target_inspector = inspect(target_engine)
    target_tables = set(target_inspector.get_table_names())
    with target_engine.connect() as connection:
        populated = [
            name
            for name in expected_tables & target_tables
            if connection.execute(
                text(f'SELECT EXISTS (SELECT 1 FROM "{name}" LIMIT 1)')
            ).scalar_one()
        ]
    if populated:
        raise ValueError(
            "Refusing to migrate into a PostgreSQL database that already contains data: "
            + ", ".join(sorted(populated))
        )

    source_metadata = MetaData()
    source_tables = {
        name: (
            source_metadata.tables[name]
            if name in source_metadata.tables
            else Table(name, source_metadata, autoload_with=source_engine)
        )
        for name in expected_tables
    }
    copied: dict[str, int] = {}
    with source_engine.connect() as source_connection, target_engine.begin() as target_connection:
        for target_table in model_tables:
            source_table = source_tables[target_table.name]
            source_columns = {column.name for column in source_table.columns}
            common_columns = [
                column.name
                for column in target_table.columns
                if column.name in source_columns
            ]
            count = 0
            result = source_connection.execution_options(stream_results=True).execute(
                select(*(source_table.c[name] for name in common_columns))
            )
            while rows := result.fetchmany(500):
                target_connection.execute(
                    insert(target_table),
                    [dict(row._mapping) for row in rows],
                )
                count += len(rows)
            copied[target_table.name] = count

        dialect = target_engine.dialect
        for table in model_tables:
            primary_key = list(table.primary_key.columns)
            if len(primary_key) != 1 or primary_key[0].type.python_type is not int:
                continue
            column_name = primary_key[0].name
            quoted_table = dialect.identifier_preparer.format_table(table)
            quoted_column = dialect.identifier_preparer.quote(column_name)
            qualified_name = f"{table.schema}.{table.name}" if table.schema else table.name
            target_connection.execute(
                text(
                    "SELECT setval("
                    "pg_get_serial_sequence(:table_name, :column_name), "
                    f"COALESCE(MAX({quoted_column}), 1), MAX({quoted_column}) IS NOT NULL"
                    f") FROM {quoted_table}"
                ),
                {"table_name": qualified_name, "column_name": column_name},
            )

    source_engine.dispose()
    target_engine.dispose()
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).parent / "instance" / "teamsphere.db",
        help="SQLite file to migrate (default: instance/teamsphere.db)",
    )
    args = parser.parse_args()
    counts = migrate(args.source)
    print("SQLite data copied to PostgreSQL:")
    for table_name, count in counts.items():
        print(f"  {table_name}: {count} rows")


if __name__ == "__main__":
    main()
