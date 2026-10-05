"""
db.py - database connection layer for HIPCMS.

PRIMARY BACKEND: MySQL 8.0  (the database described in sql/01_schema_mysql.sql)
FALLBACK:        SQLite     (offline demo copy, only if backend = sqlite)

Every front-end (gui_app.py, app.py) talks to the database ONLY through
`get_connection()` in this file, so switching backends is a config change,
not a code change.

Connection settings are read, in order of priority, from:
    1. Environment variables  HIPCMS_DB_BACKEND, HIPCMS_DB_HOST, HIPCMS_DB_PORT,
                              HIPCMS_DB_USER, HIPCMS_DB_PASSWORD, HIPCMS_DB_DATABASE
    2. app/db_config.ini      (section [database])
    3. Built-in defaults      mysql / 127.0.0.1 / 3306 / root / "" / hipcms

The wrapper below gives both backends the same small API the application
code uses:  conn.execute(sql, params) -> cursor with fetchone()/fetchall()/
lastrowid/rowcount, plus conn.commit()/rollback()/close().  Application SQL
is written with `?` placeholders; for MySQL they are converted to `%s`.
"""

import configparser
import os
import re
import sqlite3

try:
    import mysql.connector
    from mysql.connector import errorcode
    MYSQL_AVAILABLE = True
except ImportError:  # handled with a clear message in get_connection()
    mysql = None
    errorcode = None
    MYSQL_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
CONFIG_PATH = os.path.join(BASE_DIR, "db_config.ini")

# MySQL scripts (official deliverable)
MYSQL_SCRIPTS = [
    os.path.join(PROJECT_DIR, "sql", "01_schema_mysql.sql"),
    os.path.join(PROJECT_DIR, "sql", "02_sample_data.sql"),
    os.path.join(PROJECT_DIR, "sql", "03_queries_and_views.sql"),
]

# SQLite fallback files
DB_PATH = os.path.join(BASE_DIR, "hipcms.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema_sqlite.sql")
SAMPLE_DATA_PATH = os.path.join(BASE_DIR, "sample_data_sqlite.sql")


# ----------------------------------------------------------------------
# Errors: one tuple the app can catch regardless of backend
# ----------------------------------------------------------------------
if MYSQL_AVAILABLE:
    DB_ERRORS = (sqlite3.Error, mysql.connector.Error)
else:
    DB_ERRORS = (sqlite3.Error,)

# Kept for backwards compatibility with older code that caught
# db.IntegrityError - now covers every database error (FK, CHECK, UNIQUE,
# and SIGNAL SQLSTATE '45000' raised by the business-rule triggers).
IntegrityError = DB_ERRORS


class DatabaseConfigError(Exception):
    """Raised when the database cannot be reached with the current settings."""


def friendly_error(exc) -> str:
    """Turn a raw driver exception into a short, readable message."""
    if MYSQL_AVAILABLE and isinstance(exc, mysql.connector.Error):
        msg = exc.msg if getattr(exc, "msg", None) else str(exc)
        code = getattr(exc, "errno", None)
        if code == 1451:
            return ("Cannot delete this record because other records still refer to it "
                    "(FOREIGN KEY ... ON DELETE RESTRICT).\n\n" + msg)
        if code == 1452:
            return "The referenced parent record does not exist (FOREIGN KEY violation).\n\n" + msg
        if code == 1062:
            return "Duplicate value - this must be unique (UNIQUE constraint).\n\n" + msg
        if code == 3819:
            return "A CHECK constraint was violated.\n\n" + msg
        if code == 1644:  # SIGNAL SQLSTATE '45000' from a trigger
            return "Business rule (trigger) blocked this operation:\n\n" + msg
        if code == 1048:
            return "A required (NOT NULL) field was left empty.\n\n" + msg
        if code in (1292, 1366):
            return "A value has the wrong format for its column (e.g. date must be YYYY-MM-DD).\n\n" + msg
        return msg
    return str(exc)


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
def load_config() -> dict:
    cfg = {
        "backend": "mysql",
        "host": "127.0.0.1",
        "port": "3306",
        "user": "root",
        "password": "",
        "database": "hipcms",
    }
    if os.path.exists(CONFIG_PATH):
        parser = configparser.ConfigParser()
        parser.read(CONFIG_PATH)
        if parser.has_section("database"):
            for key in cfg:
                if parser.has_option("database", key):
                    cfg[key] = parser.get("database", key).strip()
    for key in cfg:
        env = os.environ.get(f"HIPCMS_DB_{key.upper()}")
        if env is not None:
            cfg[key] = env
    cfg["backend"] = cfg["backend"].lower()
    return cfg


CONFIG = load_config()


def backend() -> str:
    return CONFIG["backend"]


def describe_connection() -> str:
    if backend() == "sqlite":
        return f"SQLite (offline demo) - {DB_PATH}"
    return f"MySQL  {CONFIG['user']}@{CONFIG['host']}:{CONFIG['port']} / {CONFIG['database']}"


# ----------------------------------------------------------------------
# Row / cursor / connection wrappers (same API for both backends)
# ----------------------------------------------------------------------
class Row(dict):
    """dict that also supports positional access (row[0]) like sqlite3.Row."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class _MySQLCursor:
    def __init__(self, raw):
        self._raw = raw

    @property
    def lastrowid(self):
        return self._raw.lastrowid

    @property
    def rowcount(self):
        return self._raw.rowcount

    def fetchone(self):
        r = self._raw.fetchone()
        return Row(r) if r is not None else None

    def fetchall(self):
        return [Row(r) for r in self._raw.fetchall()]


class _MySQLConnection:
    def __init__(self, raw):
        self._raw = raw

    @staticmethod
    def _convert(sql, params):
        if params:
            # literal % must be doubled when the driver does %s formatting
            sql = sql.replace("%", "%%").replace("?", "%s")
        return sql

    def execute(self, sql, params=()):
        cur = self._raw.cursor(dictionary=True, buffered=True)
        cur.execute(self._convert(sql, params), tuple(params) if params else None)
        return _MySQLCursor(cur)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


class _SQLiteConnection:
    def __init__(self, raw):
        self._raw = raw

    def execute(self, sql, params=()):
        cur = self._raw.execute(sql, params)
        return _SQLiteCursor(cur)

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


class _SQLiteCursor:
    def __init__(self, raw):
        self._raw = raw

    @property
    def lastrowid(self):
        return self._raw.lastrowid

    @property
    def rowcount(self):
        return self._raw.rowcount

    def fetchone(self):
        r = self._raw.fetchone()
        return Row(dict(r)) if r is not None else None

    def fetchall(self):
        return [Row(dict(r)) for r in self._raw.fetchall()]


# ----------------------------------------------------------------------
# MySQL helpers
# ----------------------------------------------------------------------
def _mysql_raw(with_database=True):
    if not MYSQL_AVAILABLE:
        raise DatabaseConfigError(
            "The MySQL driver is not installed.\n\n"
            "Run:   pip install -r requirements.txt\n"
            "(or:   pip install mysql-connector-python)"
        )
    kwargs = dict(
        host=CONFIG["host"],
        port=int(CONFIG["port"]),
        user=CONFIG["user"],
        password=CONFIG["password"],
        autocommit=False,
        use_pure=True,
    )
    if with_database:
        kwargs["database"] = CONFIG["database"]
    try:
        conn = mysql.connector.connect(**kwargs)
    except mysql.connector.Error as e:
        if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise DatabaseConfigError(
                f"MySQL rejected user '{CONFIG['user']}' (wrong password?).\n"
                f"Edit app/db_config.ini and set the correct user/password."
            ) from e
        if e.errno == errorcode.ER_BAD_DB_ERROR:
            raise DatabaseConfigError(
                f"Database '{CONFIG['database']}' does not exist yet.\n"
                f"Run:  python setup_database.py"
            ) from e
        raise DatabaseConfigError(
            f"Could not connect to MySQL at {CONFIG['host']}:{CONFIG['port']}.\n"
            f"Is the MySQL server running?\n\nDetails: {e}"
        ) from e
    # Same SQL as SQLite: allow  a || ' ' || b  string concatenation.
    cur = conn.cursor()
    cur.execute("SET SESSION sql_mode = CONCAT(@@sql_mode, ',PIPES_AS_CONCAT')")
    cur.close()
    return conn


def split_mysql_script(text):
    """
    Split a .sql file into individual statements, honouring the
    DELIMITER $$ ... DELIMITER ; blocks used for the triggers
    (the mysql CLI / Workbench understand DELIMITER, drivers do not).
    """
    statements, buf, delim = [], [], ";"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            delim = stripped.split(None, 1)[1]
            continue
        if not buf and (stripped == "" or stripped.startswith("--")):
            continue
        buf.append(line)
        if stripped.endswith(delim):
            stmt = "\n".join(buf).rstrip()
            stmt = stmt[: len(stmt) - len(delim)].strip()
            if stmt:
                statements.append(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_mysql_script(path, log=print):
    """Execute one .sql file against the server (no default database)."""
    with open(path, "r", encoding="utf-8") as f:
        statements = split_mysql_script(f.read())
    conn = _mysql_raw(with_database=False)
    cur = conn.cursor()
    try:
        for stmt in statements:
            cur.execute(stmt)
            if cur.with_rows:
                cur.fetchall()
        conn.commit()
    finally:
        cur.close()
        conn.close()
    log(f"  OK  {os.path.relpath(path, PROJECT_DIR)}  ({len(statements)} statements)")


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def build_fresh_database(log=print):
    """Drop and rebuild the database from the schema + sample data."""
    if backend() == "sqlite":
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON;")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        with open(SAMPLE_DATA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        log(f"  OK  SQLite demo database rebuilt at {DB_PATH}")
        return
    if CONFIG["database"] != "hipcms":
        log(f"  NOTE: the SQL scripts create a database named 'hipcms'; "
            f"db_config.ini points at '{CONFIG['database']}'.")
    for script in MYSQL_SCRIPTS:
        run_mysql_script(script, log=log)


def get_connection():
    if backend() == "sqlite":
        if not os.path.exists(DB_PATH):
            build_fresh_database()
        raw = sqlite3.connect(DB_PATH)
        raw.execute("PRAGMA foreign_keys = ON;")
        raw.row_factory = sqlite3.Row
        return _SQLiteConnection(raw)
    return _MySQLConnection(_mysql_raw())


def test_connection():
    """Return (ok, message). Used at start-up to show a clear error."""
    try:
        conn = get_connection()
        if backend() == "sqlite":
            version = "SQLite " + sqlite3.sqlite_version
        else:
            version = "MySQL " + conn.execute("SELECT VERSION() AS v").fetchone()["v"]
        n = conn.execute("SELECT COUNT(*) AS n FROM customer").fetchone()["n"]
        conn.close()
        return True, f"{version} - connected ({n} customers)"
    except DatabaseConfigError as e:
        return False, str(e)
    except DB_ERRORS as e:
        return False, ("Connected, but the HIPCMS tables were not found.\n"
                       "Run:  python setup_database.py\n\nDetails: " + friendly_error(e))


# ----------------------------------------------------------------------
# Metadata helpers (used by the Database Records screen)
# ----------------------------------------------------------------------
def list_tables():
    conn = get_connection()
    try:
        if backend() == "sqlite":
            rows = conn.execute(
                "SELECT name AS t FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        else:
            rows = conn.execute(
                "SELECT TABLE_NAME AS t FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE='BASE TABLE' "
                "ORDER BY TABLE_NAME").fetchall()
        return [r["t"] for r in rows]
    finally:
        conn.close()


_CHECK_IN_RE = re.compile(r"`(\w+)`\s+in\s*\((.*)\)", re.IGNORECASE | re.DOTALL)


def table_columns(table):
    """
    Return a list of dicts describing each column:
      name, type, nullable, default, auto (auto-increment), pk,
      fk -> (ref_table, ref_column) or None, choices -> list or None
    """
    conn = get_connection()
    try:
        cols = []
        if backend() == "sqlite":
            fks = {r["from"]: (r["table"], r["to"])
                   for r in conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()}
            for r in conn.execute(f"PRAGMA table_info({table})").fetchall():
                is_pk = bool(r["pk"])
                cols.append(dict(
                    name=r["name"], type=r["type"].lower(), nullable=not r["notnull"],
                    default=r["dflt_value"], auto=is_pk and "int" in r["type"].lower(),
                    pk=is_pk, fk=fks.get(r["name"]), choices=None))
            return cols

        info = conn.execute(
            """SELECT COLUMN_NAME AS name, COLUMN_TYPE AS type, IS_NULLABLE AS nullable,
                      COLUMN_DEFAULT AS dflt, EXTRA AS extra, COLUMN_KEY AS ckey
               FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?
               ORDER BY ORDINAL_POSITION""", (table,)).fetchall()
        fks = {r["c"]: (r["rt"], r["rc"]) for r in conn.execute(
            """SELECT COLUMN_NAME AS c, REFERENCED_TABLE_NAME AS rt, REFERENCED_COLUMN_NAME AS rc
               FROM information_schema.KEY_COLUMN_USAGE
               WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = ?
                 AND REFERENCED_TABLE_NAME IS NOT NULL""", (table,)).fetchall()}
        choices = {}
        for r in conn.execute(
                """SELECT cc.CHECK_CLAUSE AS clause
                   FROM information_schema.CHECK_CONSTRAINTS cc
                   JOIN information_schema.TABLE_CONSTRAINTS tc
                     ON tc.CONSTRAINT_SCHEMA = cc.CONSTRAINT_SCHEMA
                    AND tc.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
                   WHERE tc.TABLE_SCHEMA = DATABASE() AND tc.TABLE_NAME = ?""",
                (table,)).fetchall():
            m = _CHECK_IN_RE.search(r["clause"].replace("\\", ""))
            if m:
                choices[m.group(1)] = re.findall(r"'([^']*)'", m.group(2))
        for r in info:
            cols.append(dict(
                name=r["name"], type=r["type"], nullable=(r["nullable"] == "YES"),
                default=r["dflt"], auto=("auto_increment" in (r["extra"] or "")),
                generated_default=("DEFAULT_GENERATED" in (r["extra"] or "")),
                pk=(r["ckey"] == "PRI"), fk=fks.get(r["name"]), choices=choices.get(r["name"])))
        return cols
    finally:
        conn.close()


def child_references(table):
    """
    Tables whose foreign keys point at `table`, with the ON DELETE rule:
    [(child_table, child_column, parent_column, delete_rule), ...]
    """
    conn = get_connection()
    try:
        if backend() == "sqlite":
            out = []
            for t in list_tables():
                for r in conn.execute(f"PRAGMA foreign_key_list({t})").fetchall():
                    if r["table"] == table:
                        out.append((t, r["from"], r["to"], r["on_delete"]))
            return out
        rows = conn.execute(
            """SELECT k.TABLE_NAME AS child, k.COLUMN_NAME AS col,
                      k.REFERENCED_COLUMN_NAME AS pcol, rc.DELETE_RULE AS rule
               FROM information_schema.KEY_COLUMN_USAGE k
               JOIN information_schema.REFERENTIAL_CONSTRAINTS rc
                 ON rc.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
                AND rc.CONSTRAINT_NAME = k.CONSTRAINT_NAME
               WHERE k.TABLE_SCHEMA = DATABASE() AND k.REFERENCED_TABLE_NAME = ?
               ORDER BY k.TABLE_NAME""", (table,)).fetchall()
        return [(r["child"], r["col"], r["pcol"], r["rule"]) for r in rows]
    finally:
        conn.close()
