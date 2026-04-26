import argparse
from pathlib import Path

from app.db.session import get_schema_mismatches, initialize_database, reset_database


def _database_file_hint() -> str:
    return str(Path("vizzy_chat.db").resolve())


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the Vizzy Chat local database.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create tables and validate the local schema.")

    status_parser = subparsers.add_parser("status", help="Show local schema mismatch status.")
    status_parser.add_argument("--verbose", action="store_true", help="Print extra mismatch details.")

    reset_parser = subparsers.add_parser("reset", help="Drop and recreate the local database tables.")
    reset_parser.add_argument("--yes", action="store_true", help="Confirm destructive reset.")

    args = parser.parse_args()

    if args.command == "init":
        initialize_database()
        print("Database initialized successfully.")
        return

    if args.command == "status":
        mismatches = get_schema_mismatches()
        if not mismatches:
            print("Database schema is up to date.")
            return
        print("Database schema mismatch detected.")
        if args.verbose:
            for table_name, columns in mismatches.items():
                print(f"- {table_name}: missing {', '.join(columns)}")
        return

    if args.command == "reset":
        if not args.yes:
            raise SystemExit(
                "Reset is destructive. Re-run with `python -m app.db.manage reset --yes` "
                f"to recreate the local database at {_database_file_hint()}."
            )
        reset_database()
        print("Database reset successfully.")


if __name__ == "__main__":
    main()
