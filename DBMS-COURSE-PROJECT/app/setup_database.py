"""
setup_database.py - create (or reset) the HIPCMS database on MySQL.

Runs, in order:
    sql/01_schema_mysql.sql       tables, constraints, indexes, triggers
    sql/02_sample_data.sql        sample records
    sql/03_queries_and_views.sql  report views (+ example queries)

Usage:
    python setup_database.py          # asks for confirmation
    python setup_database.py --yes    # no prompt (drops & recreates hipcms)

Connection settings come from app/db_config.ini (or HIPCMS_DB_* env vars).
"""
import sys

import db


def main():
    print("HIPCMS database setup")
    print("Target:", db.describe_connection())
    if "--yes" not in sys.argv:
        ans = input("This DROPS and recreates the database with sample data. Continue? [y/N] ")
        if ans.strip().lower() != "y":
            print("Cancelled.")
            return 1
    try:
        db.build_fresh_database()
    except db.DatabaseConfigError as e:
        print("\nERROR:", e)
        return 1
    except db.DB_ERRORS as e:
        print("\nERROR while running SQL:", db.friendly_error(e))
        return 1
    ok, msg = db.test_connection()
    print(("\nSUCCESS: " if ok else "\nPROBLEM: ") + msg)
    if ok:
        conn = db.get_connection()
        print("\nRow counts:")
        for t in db.list_tables():
            n = conn.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"]
            print(f"  {t:<16} {n}")
        conn.close()
        print("\nNext:  python gui_app.py")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
