"""
HIPCMS - Tkinter GUI front-end connected to MySQL

Run:
    python setup_database.py     # once: creates the hipcms MySQL database
    python gui_app.py            # start the UI

The connection settings live in db_config.ini (see db.py). Both front-ends
(gui_app.py and the console app.py) work on the same MySQL database, so a
change made here is immediately visible in MySQL Workbench / the mysql CLI.

Login with any seeded account (admin/agent1/agent2/assessor1/assessor2) and
password 'password'. Log in as admin to use Delete on the Database Records tab.

Tabs
  Database Records        - generic INSERT / VIEW / DELETE on every table,
                            with a live log of the exact SQL sent to MySQL
  Customers & Dependants  - add / delete customers and dependants
  Policies & Premiums     - issue policies, collect premiums
  Claims                  - submit, verify, assess/decide, settle
  Appeals                 - file / resolve appeals
  Reports                 - the 7 report views
"""
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import random

import db
from validators import is_valid_email, is_valid_phone, is_valid_date, is_positive_number

FONT_NORMAL = ("Segoe UI", 10)
FONT_HEADER = ("Segoe UI", 13, "bold")
FONT_TAB = ("Segoe UI", 10, "bold")
BG = "#f4f6f8"
ACCENT = "#2c3e50"
DANGER = "#b03a2e"
SUCCESS = "#1e8449"
MONO = ("Consolas", 9)

current_user = {}


# ======================================================================
# DB helpers
# ======================================================================
def query(sql, params=()):
    """Run a SELECT and return a list of dict-like rows ([] on error)."""
    try:
        conn = db.get_connection()
    except db.DatabaseConfigError as e:
        messagebox.showerror("Database connection", str(e))
        return []
    try:
        return conn.execute(sql, params).fetchall()
    except db.DB_ERRORS as e:
        messagebox.showerror("Database error", db.friendly_error(e))
        return []
    finally:
        conn.close()


def execute(sql, params=()):
    """Run a write statement. Returns (success, lastrowid_or_None, message)."""
    try:
        conn = db.get_connection()
    except db.DatabaseConfigError as e:
        return False, None, str(e)
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return True, cur.lastrowid, "OK"
    except db.DB_ERRORS as e:
        conn.rollback()
        return False, None, db.friendly_error(e)
    finally:
        conn.close()


def execute_or_warn(sql, params=(), title="Could not save"):
    """execute() that shows a message box on failure. Returns True/False."""
    ok, _, msg = execute(sql, params)
    if not ok:
        messagebox.showerror(title, msg)
    return ok


def next_number(prefix):
    return f"{prefix}-{date.today().year}-{random.randint(1000, 9999)}"


def fill_tree(tree, rows, columns=None, null_text=""):
    tree.delete(*tree.get_children())
    cols = list(rows[0].keys()) if rows else list(columns or tree["columns"])
    tree["columns"] = cols
    tree["show"] = "headings"
    sample = rows[:200]
    for c in cols:
        tree.heading(c, text=c)
        longest = max([len(str(c))] + [len(str(r[c])) for r in sample])
        tree.column(c, width=max(70, min(260, 8 * longest + 18)), minwidth=50, stretch=False, anchor="w")
    for r in rows:
        tree.insert("", "end", values=[null_text if r[c] is None else r[c] for c in cols])


def selected_value(tree, col_name):
    """Return the value of `col_name` from the selected treeview row, or None."""
    sel = tree.selection()
    if not sel:
        return None
    cols = tree["columns"]
    values = tree.item(sel[0], "values")
    if col_name not in cols:
        return None
    return values[list(cols).index(col_name)]


# ======================================================================
# Reusable little form dialog
# ======================================================================
class FormDialog(tk.Toplevel):
    """
    Generic modal form. `fields` is a list of (label, kind, options) tuples:
      kind == "entry"  -> options unused
      kind == "combo"  -> options = list of choices
      kind == "text"   -> multi-purpose free text (used same as entry here)
    Calling .result after `wait_window()` gives a dict {label: value} or None
    if cancelled.
    """
    def __init__(self, parent, title, fields, initial=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG, padx=16, pady=16)
        self.resizable(False, False)
        self.result = None
        self.vars = {}
        initial = initial or {}

        for i, (label, kind, options) in enumerate(fields):
            tk.Label(self, text=label, bg=BG, font=FONT_NORMAL).grid(row=i, column=0, sticky="w", pady=4)
            if kind == "combo":
                var = tk.StringVar(value=initial.get(label, options[0]))
                w = ttk.Combobox(self, textvariable=var, values=options, state="readonly", width=28)
            else:
                var = tk.StringVar(value=initial.get(label, ""))
                w = tk.Entry(self, textvariable=var, width=30, font=FONT_NORMAL)
            w.grid(row=i, column=1, pady=4, padx=(10, 0))
            self.vars[label] = var

        btn_row = len(fields)
        btns = tk.Frame(self, bg=BG)
        btns.grid(row=btn_row, column=0, columnspan=2, pady=(14, 0))
        tk.Button(btns, text="OK", width=10, command=self._ok, bg=ACCENT, fg="white").pack(side="left", padx=6)
        tk.Button(btns, text="Cancel", width=10, command=self.destroy).pack(side="left", padx=6)

        self.transient(parent)
        center_on_parent(self, parent)
        self.grab_set()

    def _ok(self):
        self.result = {k: v.get().strip() for k, v in self.vars.items()}
        self.destroy()


def center_on_parent(win, parent):
    """Place a dialog in the middle of its parent window."""
    win.update_idletasks()
    top = parent.winfo_toplevel()
    x = top.winfo_rootx() + (top.winfo_width() - win.winfo_reqwidth()) // 2
    y = top.winfo_rooty() + (top.winfo_height() - win.winfo_reqheight()) // 3
    win.geometry(f"+{max(0, x)}+{max(0, y)}")


def ask_form(parent, title, fields, initial=None):
    dlg = FormDialog(parent, title, fields, initial)
    parent.wait_window(dlg)
    return dlg.result


# ======================================================================
# Login window
# ======================================================================
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HIPCMS - Login")
        self.geometry("380x300")
        self.configure(bg=BG)
        self.resizable(False, False)

        tk.Label(self, text="Health Insurance Policy &\nClaims Management System",
                 font=FONT_HEADER, bg=BG, fg=ACCENT, justify="center").pack(pady=(30, 10))
        tk.Label(self, text="(demo: admin / agent1 / agent2 / assessor1 / assessor2,\npassword: 'password')",
                 font=("Segoe UI", 8), bg=BG, fg="#666").pack(pady=(0, 20))

        form = tk.Frame(self, bg=BG)
        form.pack()
        tk.Label(form, text="Username:", bg=BG, font=FONT_NORMAL).grid(row=0, column=0, sticky="e", pady=6)
        self.user_var = tk.StringVar()
        tk.Entry(form, textvariable=self.user_var, font=FONT_NORMAL).grid(row=0, column=1, pady=6, padx=6)

        tk.Label(form, text="Password:", bg=BG, font=FONT_NORMAL).grid(row=1, column=0, sticky="e", pady=6)
        self.pw_var = tk.StringVar()
        tk.Entry(form, textvariable=self.pw_var, show="*", font=FONT_NORMAL).grid(row=1, column=1, pady=6, padx=6)

        tk.Button(self, text="Login", width=16, bg=ACCENT, fg="white",
                  command=self.try_login).pack(pady=20)
        self.status = tk.Label(self, text="", fg="red", bg=BG, font=FONT_NORMAL)
        self.status.pack()

        self.bind("<Return>", lambda e: self.try_login())

    def try_login(self):
        global current_user
        username = self.user_var.get().strip()
        password = self.pw_var.get().strip()
        rows = query("SELECT * FROM users WHERE username=? AND is_active=1", (username,))
        if rows and password == "password":
            current_user = dict(rows[0])
            self.destroy()
            MainApp().mainloop()
        else:
            self.status.config(text="Invalid username or password.")


# ======================================================================
# Main application window
# ======================================================================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"HIPCMS - logged in as {current_user['full_name']} ({current_user['role']})")
        self.geometry("1250x760")
        self.configure(bg=BG)

        style = ttk.Style(self)
        style.configure("TNotebook.Tab", font=FONT_TAB, padding=(14, 8))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

        header = tk.Frame(self, bg=ACCENT, height=44)
        header.pack(fill="x")
        tk.Label(header, text="HIPCMS", font=("Segoe UI", 14, "bold"), bg=ACCENT, fg="white").pack(side="left", padx=16, pady=6)
        tk.Label(header, text=f"{current_user['full_name']}  |  {current_user['role']}", bg=ACCENT, fg="white",
                 font=FONT_NORMAL).pack(side="right", padx=16)

        nb = ttk.Notebook(self)

        self.records_tab = RecordsTab(nb)
        self.customers_tab = CustomersTab(nb)
        self.policies_tab = PoliciesTab(nb)
        self.claims_tab = ClaimsTab(nb)
        self.appeals_tab = AppealsTab(nb)
        self.reports_tab = ReportsTab(nb)

        nb.add(self.records_tab, text="Database Records")
        nb.add(self.customers_tab, text="Customers & Dependants")
        nb.add(self.policies_tab, text="Policies & Premiums")
        nb.add(self.claims_tab, text="Claims")
        nb.add(self.appeals_tab, text="Appeals")
        nb.add(self.reports_tab, text="Reports")

        status_bar = tk.Frame(self, bg="#e8e8e8", bd=1, relief="sunken")
        status_bar.pack(fill="x", side="bottom")
        self.status = tk.Label(status_bar, text="Ready.", anchor="w", bg="#e8e8e8", font=("Segoe UI", 9))
        self.status.pack(side="left", fill="x", expand=True, padx=4)
        tk.Label(status_bar, text="DB: " + db.describe_connection(), anchor="e", bg="#e8e8e8",
                 fg="#1a5276", font=("Segoe UI", 9, "bold")).pack(side="right", padx=8)
        # Notebook is packed after the status bar so the bar is never pushed off-screen
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        MainApp.instance = self

    def set_status(self, text, ok=True):
        self.status.config(text=text, fg=("#1a7a1a" if ok else "#b00020"))


def app_status(text, ok=True):
    if hasattr(MainApp, "instance"):
        MainApp.instance.set_status(text, ok)


# ======================================================================
# Tab: Database Records  (INSERT / VIEW / DELETE on any MySQL table)
# ======================================================================
FK_LABEL_PREFERENCE = ["policy_number", "claim_number", "plan_name", "hospital_name",
                       "full_name", "username", "document_type", "treatment_name"]


def sql_literal(value):
    """Render a Python value as a SQL literal - used only for the on-screen log."""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def fk_options(ref_table, ref_col):
    """'id - readable label' choices for a foreign-key dropdown."""
    cols = [c["name"] for c in db.table_columns(ref_table)]
    if "first_name" in cols and "last_name" in cols:
        label = "first_name || ' ' || last_name"
    else:
        label = next((c for c in FK_LABEL_PREFERENCE if c in cols), ref_col)
    rows = query(f"SELECT {ref_col} AS id, {label} AS label FROM {ref_table} ORDER BY {ref_col} LIMIT 1000")
    return [f"{r['id']} - {r['label']}" for r in rows]


class InsertRecordDialog(tk.Toplevel):
    """
    Insert form generated from the table's real MySQL metadata
    (information_schema): one input per column, with
      * CHECK (col IN (...)) constraints shown as drop-downs,
      * FOREIGN KEY columns shown as drop-downs of existing parent rows,
      * required (NOT NULL, no default) columns marked with *,
      * AUTO_INCREMENT keys and auto timestamps left for MySQL to fill.
    .result -> (column_list, value_list) or None if cancelled.
    """

    def __init__(self, parent, table):
        super().__init__(parent)
        self.title(f"Insert record into `{table}`")
        self.configure(bg=BG, padx=16, pady=12)
        self.resizable(False, False)
        self.table = table
        self.result = None
        self.inputs = []  # (column_meta, tk variable, kind)

        all_cols = db.table_columns(table)
        self.columns = [c for c in all_cols if not c["auto"] and not c.get("generated_default")]
        skipped = [c["name"] for c in all_cols if c not in self.columns]

        tk.Label(self, text=f"New row for table: {table}", font=FONT_HEADER, bg=BG, fg=ACCENT)\
            .grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(self, text="* = required.   Leave optional fields blank to store NULL / the column default."
                 + (f"\nFilled automatically by MySQL: {', '.join(skipped)}" if skipped else ""),
                 font=("Segoe UI", 8), bg=BG, fg="#555", justify="left")\
            .grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        for i, col in enumerate(self.columns, start=2):
            required = (not col["nullable"]) and col["default"] is None
            tk.Label(self, text=col["name"] + (" *" if required else ""), bg=BG,
                     font=(FONT_NORMAL[0], 10, "bold" if required else "normal"))\
                .grid(row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            if col["choices"]:
                values = ([""] if not required else []) + col["choices"]
                if col["default"] is not None and str(col["default"]).strip("'") in values:
                    var.set(str(col["default"]).strip("'"))
                elif required:
                    var.set(values[0])
                w = ttk.Combobox(self, textvariable=var, values=values, state="readonly", width=34)
                kind, hint = "choice", "CHECK: " + "/".join(col["choices"])[:40]
            elif col["fk"]:
                ref_t, ref_c = col["fk"]
                values = ([""] if col["nullable"] else []) + fk_options(ref_t, ref_c)
                w = ttk.Combobox(self, textvariable=var, values=values, state="readonly", width=34)
                if values and required:
                    var.set(values[0])
                kind, hint = "fk", f"FK -> {ref_t}.{ref_c}"
            else:
                if col["default"] is not None:
                    var.set(str(col["default"]).strip("'"))
                w = tk.Entry(self, textvariable=var, width=37, font=FONT_NORMAL)
                kind = "entry"
                t = col["type"].lower()
                hint = col["type"] + ("  (YYYY-MM-DD)" if t == "date" else "")
            w.grid(row=i, column=1, pady=3, padx=(10, 6))
            tk.Label(self, text=hint, bg=BG, fg="#888", font=("Segoe UI", 8)).grid(row=i, column=2, sticky="w")
            self.inputs.append((col, var, kind))

        btns = tk.Frame(self, bg=BG)
        btns.grid(row=len(self.columns) + 2, column=0, columnspan=3, pady=(14, 0))
        tk.Button(btns, text="INSERT", width=12, command=self._ok, bg=SUCCESS, fg="white").pack(side="left", padx=6)
        tk.Button(btns, text="Cancel", width=10, command=self.destroy).pack(side="left", padx=6)

        self.transient(parent)
        center_on_parent(self, parent)
        self.grab_set()

    def _ok(self):
        cols, vals, problems = [], [], []
        for col, var, kind in self.inputs:
            raw = var.get().strip()
            required = (not col["nullable"]) and col["default"] is None
            if raw == "":
                if required:
                    problems.append(f"{col['name']} is required")
                continue  # let MySQL apply NULL / DEFAULT
            value = raw.split(" - ")[0] if kind == "fk" else raw
            if kind == "fk" and value.isdigit():
                value = int(value)
            t = col["type"].lower()
            if t == "date" and not is_valid_date(value):
                problems.append(f"{col['name']} must be a date YYYY-MM-DD")
            elif (t.startswith(("int", "tinyint", "smallint", "bigint", "decimal", "double", "float"))
                  and kind == "entry"):
                try:
                    float(value)
                except ValueError:
                    problems.append(f"{col['name']} must be a number")
            elif col["name"] == "email" and not is_valid_email(str(value)):
                problems.append("email is not a valid address")
            elif col["name"] == "phone" and not is_valid_phone(str(value)):
                problems.append("phone must be exactly 10 digits")
            cols.append(col["name"])
            vals.append(value)
        if problems:
            messagebox.showerror("Please fix", "\n".join("- " + p for p in problems), parent=self)
            return
        if not cols:
            messagebox.showerror("Nothing to insert", "Fill in at least one field.", parent=self)
            return
        self.result = (cols, vals)
        self.destroy()


class RecordsTab(tk.Frame):
    """
    Generic record manager for the Review-3 UI demonstration:
      VIEW   - SELECT * FROM <table>  (live from MySQL, with row count)
      INSERT - auto-generated form   -> INSERT INTO <table> (...) VALUES (...)
      DELETE - selected row          -> DELETE FROM <table> WHERE <pk> = ?
    Every statement is written to the SQL activity log together with the
    table's COUNT(*) before and after, and "Verify in DB" re-reads the row
    through a brand-new MySQL connection to prove the change was committed.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.table_var = tk.StringVar()
        self.last_table = None
        self.last_pk_value = None
        self.last_action = None
        self.columns_meta = []

        # ---- top toolbar -------------------------------------------------
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", pady=(4, 6))
        tk.Label(bar, text="Table:", font=FONT_TAB, bg=BG).pack(side="left")
        self.tables = db.list_tables()
        self.table_combo = ttk.Combobox(bar, textvariable=self.table_var, values=self.tables,
                                        state="readonly", width=20)
        self.table_combo.pack(side="left", padx=(6, 12))
        self.table_combo.bind("<<ComboboxSelected>>", lambda e: self.view_records())

        tk.Button(bar, text="View Records", bg=ACCENT, fg="white", padx=12,
                  command=self.view_records).pack(side="left", padx=3)
        tk.Button(bar, text="+ Insert Record", bg=SUCCESS, fg="white", padx=12,
                  command=self.insert_record).pack(side="left", padx=3)
        tk.Button(bar, text="Delete Selected", bg=DANGER, fg="white", padx=12,
                  command=self.delete_record).pack(side="left", padx=3)
        tk.Button(bar, text="Verify in DB", padx=12,
                  command=self.verify_in_db).pack(side="left", padx=(12, 3))

        self.count_label = tk.Label(bar, text="", font=FONT_TAB, bg=BG, fg="#1a5276")
        self.count_label.pack(side="right", padx=6)

        # ---- results grid ------------------------------------------------
        grid = tk.Frame(self, bg=BG)
        grid.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(grid, selectmode="browse")
        vsb = ttk.Scrollbar(grid, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(grid, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        grid.rowconfigure(0, weight=1)
        grid.columnconfigure(0, weight=1)
        self.tree.tag_configure("new", background="#d5f5e3")

        # ---- SQL activity log --------------------------------------------
        log_frame = tk.LabelFrame(self, text=" SQL activity log - statements sent to the database ",
                                  bg=BG, font=FONT_TAB, fg=ACCENT)
        log_frame.pack(fill="x", pady=(8, 0))
        self.log = tk.Text(log_frame, height=9, font=MONO, bg="#1e1e1e", fg="#d4d4d4",
                           insertbackground="white", wrap="word", state="disabled")
        self.log.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        log_sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        log_sb.pack(side="left", fill="y", pady=6)
        self.log.configure(yscrollcommand=log_sb.set)
        for tag, colour in (("sql", "#9cdcfe"), ("ok", "#6a9955"), ("err", "#f44747"),
                            ("info", "#ce9178"), ("time", "#808080")):
            self.log.tag_configure(tag, foreground=colour)
        tk.Button(log_frame, text="Clear", command=self.clear_log).pack(side="right", padx=6, anchor="n", pady=6)

        self.write_log(f"Connected to {db.describe_connection()}", "info")
        if self.tables:
            self.table_var.set("customer" if "customer" in self.tables else self.tables[0])
            self.view_records(log=False)

    # ---- helpers ---------------------------------------------------------
    def write_log(self, text, tag="sql"):
        from datetime import datetime
        self.log.configure(state="normal")
        self.log.insert("end", datetime.now().strftime("[%H:%M:%S] "), "time")
        self.log.insert("end", text + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def pk_column(self, table):
        for c in self.columns_meta:
            if c["pk"]:
                return c["name"]
        return None

    def count_rows(self, table):
        r = query(f"SELECT COUNT(*) AS n FROM {table}")
        return r[0]["n"] if r else 0

    # ---- VIEW --------------------------------------------------------------
    def view_records(self, log=True, highlight_pk=None):
        table = self.table_var.get()
        if not table:
            return
        self.columns_meta = db.table_columns(table)
        pk = self.pk_column(table)
        sql = f"SELECT * FROM {table}" + (f" ORDER BY {pk}" if pk else "")
        rows = query(sql)
        fill_tree(self.tree, rows, columns=[c["name"] for c in self.columns_meta], null_text="NULL")
        for c in self.tree["columns"]:
            meta = next((m for m in self.columns_meta if m["name"] == c), None)
            label = c + (" (PK)" if meta and meta["pk"] else "") + (" (FK)" if meta and meta["fk"] else "")
            self.tree.heading(c, text=label)
            self.tree.column(c, width=max(int(self.tree.column(c, "width")), 8 * len(label) + 18))
        self.count_label.config(text=f"{len(rows)} row(s) in `{table}`")
        if log:
            self.write_log(f"{sql};", "sql")
            self.write_log(f"  -> {len(rows)} row(s) returned", "ok")
        if highlight_pk is not None and pk:
            idx = list(self.tree["columns"]).index(pk)
            for item in self.tree.get_children():
                if str(self.tree.item(item, "values")[idx]) == str(highlight_pk):
                    self.tree.item(item, tags=("new",))
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    break
        app_status(f"Viewing `{table}` - {len(rows)} row(s).")

    # ---- INSERT ------------------------------------------------------------
    def insert_record(self):
        table = self.table_var.get()
        if not table:
            messagebox.showwarning("Choose a table", "Choose a table first.")
            return
        dlg = InsertRecordDialog(self, table)
        self.wait_window(dlg)
        if not dlg.result:
            return
        cols, vals = dlg.result
        before = self.count_rows(table)
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})"
        shown = f"INSERT INTO {table} ({', '.join(cols)})\n           VALUES ({', '.join(sql_literal(v) for v in vals)});"
        self.write_log(shown, "sql")
        ok, new_id, msg = execute(sql, vals)
        if not ok:
            self.write_log("  -> REJECTED by MySQL: " + msg.replace("\n", " "), "err")
            messagebox.showerror("Insert rejected by the database", msg)
            app_status(f"Insert into `{table}` rejected.", ok=False)
            return
        after = self.count_rows(table)
        pk = self.pk_column(table)
        self.write_log(f"  -> 1 row inserted, {pk} = {new_id}   |   COUNT(*) {before} -> {after}   (COMMIT done)", "ok")
        self.last_table, self.last_pk_value, self.last_action = table, new_id, "insert"
        self.view_records(log=False, highlight_pk=new_id)
        app_status(f"Inserted into `{table}`: {pk}={new_id}. Row count {before} -> {after}.")

    # ---- DELETE ------------------------------------------------------------
    def delete_record(self):
        table = self.table_var.get()
        if current_user.get("role") != "ADMIN":
            messagebox.showwarning("Not allowed", "Only an ADMIN user can delete records.\nLog in as 'admin'.")
            return
        pk = self.pk_column(table)
        pk_value = selected_value(self.tree, pk) if pk else None
        if pk_value is None:
            messagebox.showwarning("Select a row", "Click the row you want to delete first.")
            return
        if str(pk_value).isdigit():
            pk_value = int(pk_value)

        # Show the user what the foreign keys will do before deleting.
        effects, blocked = [], False
        for child, col, pcol, rule in db.child_references(table):
            n = query(f"SELECT COUNT(*) AS n FROM {child} WHERE {col} = ?", (pk_value,))
            n = n[0]["n"] if n else 0
            if n:
                effects.append(f"  - {n} row(s) in `{child}` ({rule})")
                blocked = blocked or rule.upper() in ("RESTRICT", "NO ACTION")
        msg = f"DELETE FROM {table} WHERE {pk} = {sql_literal(pk_value)};\n\n"
        if effects:
            msg += "Related records:\n" + "\n".join(effects) + "\n\n"
            msg += ("CASCADE rows will be deleted too, SET NULL rows will be unlinked.\n"
                    + ("RESTRICT rows exist, so MySQL is expected to REFUSE this delete.\n" if blocked else ""))
        else:
            msg += "No other records refer to this row.\n"
        msg += "\nProceed?"
        if not messagebox.askyesno("Confirm delete", msg, icon="warning"):
            return

        before = self.count_rows(table)
        self.write_log(f"DELETE FROM {table} WHERE {pk} = {sql_literal(pk_value)};", "sql")
        ok, _, err = execute(f"DELETE FROM {table} WHERE {pk} = ?", (pk_value,))
        if not ok:
            self.write_log("  -> REJECTED by MySQL: " + err.replace("\n", " "), "err")
            messagebox.showerror("Delete rejected by the database", err)
            app_status(f"Delete from `{table}` rejected.", ok=False)
            return
        after = self.count_rows(table)
        self.write_log(f"  -> {before - after} row(s) deleted   |   COUNT(*) {before} -> {after}   (COMMIT done)", "ok")
        self.last_table, self.last_pk_value, self.last_action = table, pk_value, "delete"
        self.view_records(log=False)
        app_status(f"Deleted {pk}={pk_value} from `{table}`. Row count {before} -> {after}.")

    # ---- VERIFY ------------------------------------------------------------
    def verify_in_db(self):
        """Re-read through a NEW connection - proves the change is committed in MySQL."""
        table = self.last_table or self.table_var.get()
        if not table:
            return
        meta = db.table_columns(table)
        pk = next((c["name"] for c in meta if c["pk"]), None)
        pk_value = self.last_pk_value
        if pk_value is None:
            pk_value = selected_value(self.tree, pk) if pk else None
        try:
            conn = db.get_connection()  # brand-new session
            n = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
            self.write_log(f"[new connection] SELECT COUNT(*) FROM {table};  -> {n}", "info")
            if pk and pk_value is not None:
                row = conn.execute(f"SELECT * FROM {table} WHERE {pk} = ?", (pk_value,)).fetchone()
                self.write_log(f"[new connection] SELECT * FROM {table} WHERE {pk} = {sql_literal(pk_value)};", "info")
                if row:
                    preview = ", ".join(f"{k}={v}" for k, v in list(row.items())[:6])
                    self.write_log(f"  -> FOUND: {preview}", "ok")
                else:
                    self.write_log("  -> 0 rows: record does not exist in the database", "ok")
            conn.close()
        except (db.DatabaseConfigError,) + db.DB_ERRORS as e:
            self.write_log("  -> verify failed: " + str(e), "err")


# ======================================================================
# Tab: Customers & Dependants
# ======================================================================
class CustomersTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        left = tk.Frame(self, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(self, bg=BG)
        right.pack(side="right", fill="y")

        tk.Label(left, text="Customers", font=FONT_HEADER, bg=BG).pack(anchor="w")
        self.tree = ttk.Treeview(left)
        self.tree.pack(fill="both", expand=True, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        tk.Label(left, text="Dependants of selected customer", font=FONT_HEADER, bg=BG).pack(anchor="w", pady=(10, 0))
        self.dep_tree = ttk.Treeview(left, height=6)
        self.dep_tree.pack(fill="x", pady=6)

        tk.Button(right, text="+ Add Customer", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.add_customer).pack(fill="x", padx=10, pady=(0, 8))
        tk.Button(right, text="+ Add Dependant", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.add_dependant).pack(fill="x", padx=10, pady=8)
        tk.Button(right, text="Delete Customer", bg=DANGER, fg="white", padx=14, pady=6,
                  command=self.delete_customer).pack(fill="x", padx=10, pady=(20, 8))
        tk.Button(right, text="Delete Dependant", bg=DANGER, fg="white", padx=14, pady=6,
                  command=self.delete_dependant).pack(fill="x", padx=10, pady=8)
        tk.Button(right, text="Refresh", padx=14, pady=6, command=self.refresh).pack(fill="x", padx=10, pady=(20, 8))

        self.selected_customer_id = None
        self.refresh()

    def refresh(self):
        rows = query("SELECT customer_id, first_name, last_name, phone, email, city, state FROM customer ORDER BY customer_id")
        fill_tree(self.tree, rows)
        self.dep_tree.delete(*self.dep_tree.get_children())

    def on_select(self, _evt=None):
        cust_id = selected_value(self.tree, "customer_id")
        self.selected_customer_id = cust_id
        if cust_id:
            deps = query("SELECT dependant_id, first_name, last_name, dob, gender, relationship FROM dependant WHERE customer_id=?", (cust_id,))
            fill_tree(self.dep_tree, deps)

    def add_customer(self):
        fields = [
            ("First name", "entry", None), ("Last name", "entry", None),
            ("DOB (YYYY-MM-DD)", "entry", None), ("Gender", "combo", ["M", "F", "O"]),
            ("ID proof number", "entry", None), ("Phone (10 digits)", "entry", None),
            ("Email", "entry", None), ("Address line", "entry", None),
            ("City", "entry", None), ("State", "entry", None), ("Pincode", "entry", None),
        ]
        data = ask_form(self, "Add Customer", fields)
        if not data:
            return
        if not is_valid_date(data["DOB (YYYY-MM-DD)"]):
            messagebox.showerror("Invalid input", "DOB must be YYYY-MM-DD.")
            return
        if not is_valid_phone(data["Phone (10 digits)"]):
            messagebox.showerror("Invalid input", "Phone must be exactly 10 digits.")
            return
        if not is_valid_email(data["Email"]):
            messagebox.showerror("Invalid input", "Enter a valid email address.")
            return
        ok, rowid, msg = execute(
            """INSERT INTO customer (first_name,last_name,dob,gender,id_proof_number,phone,email,
               address_line,city,state,pincode) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (data["First name"], data["Last name"], data["DOB (YYYY-MM-DD)"], data["Gender"],
             data["ID proof number"], data["Phone (10 digits)"], data["Email"], data["Address line"],
             data["City"], data["State"], data["Pincode"]),
        )
        if ok:
            app_status(f"Customer created (customer_id={rowid}).")
            self.refresh()
        else:
            messagebox.showerror("Could not save", msg)
            app_status("Failed to add customer.", ok=False)

    def add_dependant(self):
        if not self.selected_customer_id:
            messagebox.showwarning("Select a customer", "Select a customer in the list first.")
            return
        fields = [
            ("First name", "entry", None), ("Last name", "entry", None),
            ("DOB (YYYY-MM-DD)", "entry", None), ("Gender", "combo", ["M", "F", "O"]),
            ("Relationship", "combo", ["SPOUSE", "SON", "DAUGHTER", "FATHER", "MOTHER", "OTHER"]),
        ]
        data = ask_form(self, f"Add Dependant (customer_id={self.selected_customer_id})", fields)
        if not data:
            return
        if not is_valid_date(data["DOB (YYYY-MM-DD)"]):
            messagebox.showerror("Invalid input", "DOB must be YYYY-MM-DD.")
            return
        ok, rowid, msg = execute(
            "INSERT INTO dependant (customer_id, first_name, last_name, dob, gender, relationship) VALUES (?,?,?,?,?,?)",
            (self.selected_customer_id, data["First name"], data["Last name"],
             data["DOB (YYYY-MM-DD)"], data["Gender"], data["Relationship"]),
        )
        if ok:
            app_status(f"Dependant added (dependant_id={rowid}).")
            self.on_select()
        else:
            messagebox.showerror("Could not save", msg)
            app_status("Failed to add dependant.", ok=False)


    def delete_customer(self):
        cust_id = selected_value(self.tree, "customer_id")
        if not cust_id:
            messagebox.showwarning("Select a customer", "Select a customer in the list first.")
            return
        n_pol = query("SELECT COUNT(*) AS n FROM policy WHERE customer_id=?", (cust_id,))
        n_dep = query("SELECT COUNT(*) AS n FROM dependant WHERE customer_id=?", (cust_id,))
        n_pol = n_pol[0]["n"] if n_pol else 0
        n_dep = n_dep[0]["n"] if n_dep else 0
        if n_pol:
            messagebox.showwarning(
                "Cannot delete",
                f"Customer {cust_id} still holds {n_pol} policy record(s).\n\n"
                "policy.customer_id is ON DELETE RESTRICT, so MySQL protects this customer.")
            return
        if not messagebox.askyesno(
                "Confirm delete",
                f"Delete customer {cust_id}?\n\n"
                f"{n_dep} dependant(s) will also be removed (ON DELETE CASCADE)."):
            return
        ok, _, msg = execute("DELETE FROM customer WHERE customer_id=?", (cust_id,))
        if ok:
            app_status(f"Customer {cust_id} deleted ({n_dep} dependant(s) cascaded).")
            self.refresh()
        else:
            messagebox.showerror("Could not delete", msg)

    def delete_dependant(self):
        dep_id = selected_value(self.dep_tree, "dependant_id")
        if not dep_id:
            messagebox.showwarning("Select a dependant", "Select a dependant in the lower list first.")
            return
        if not messagebox.askyesno("Confirm delete",
                                   f"Delete dependant {dep_id}?\n\nClaims that referred to this dependant "
                                   "keep their record (dependant_id is set to NULL)."):
            return
        ok, _, msg = execute("DELETE FROM dependant WHERE dependant_id=?", (dep_id,))
        if ok:
            app_status(f"Dependant {dep_id} deleted.")
            self.on_select()
        else:
            messagebox.showerror("Could not delete", msg)


# ======================================================================
# Tab: Policies & Premiums
# ======================================================================
class PoliciesTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        left = tk.Frame(self, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(self, bg=BG)
        right.pack(side="right", fill="y")

        tk.Label(left, text="Policies", font=FONT_HEADER, bg=BG).pack(anchor="w")
        self.tree = ttk.Treeview(left)
        self.tree.pack(fill="both", expand=True, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        tk.Label(left, text="Premium installments of selected policy", font=FONT_HEADER, bg=BG).pack(anchor="w", pady=(10, 0))
        self.prem_tree = ttk.Treeview(left, height=6)
        self.prem_tree.pack(fill="x", pady=6)

        tk.Button(right, text="+ Issue Policy", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.issue_policy).pack(fill="x", padx=10, pady=(0, 8))
        tk.Button(right, text="Collect Premium", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.collect_premium).pack(fill="x", padx=10, pady=8)
        tk.Button(right, text="Refresh", padx=14, pady=6, command=self.refresh).pack(fill="x", padx=10, pady=8)

        self.selected_policy_id = None
        self.refresh()

    def refresh(self):
        rows = query("""SELECT p.policy_id, p.policy_number, c.first_name||' '||c.last_name AS holder,
                                pm.plan_name, p.sum_insured, p.start_date, p.end_date, p.status
                         FROM policy p JOIN customer c ON p.customer_id=c.customer_id
                         JOIN plan_master pm ON p.plan_id=pm.plan_id ORDER BY p.policy_id""")
        fill_tree(self.tree, rows)
        self.prem_tree.delete(*self.prem_tree.get_children())

    def on_select(self, _evt=None):
        pid = selected_value(self.tree, "policy_id")
        self.selected_policy_id = pid
        if pid:
            prems = query("SELECT premium_id, due_date, amount_due, status FROM premium WHERE policy_id=?", (pid,))
            fill_tree(self.prem_tree, prems)

    def issue_policy(self):
        plans = query("SELECT plan_id, plan_name FROM plan_master WHERE is_active=1")
        plan_choices = [f"{p['plan_id']} - {p['plan_name']}" for p in plans]
        fields = [
            ("Customer ID", "entry", None),
            ("Plan", "combo", plan_choices),
            ("Sum insured", "entry", None),
            ("Start date (YYYY-MM-DD)", "entry", None),
            ("End date (YYYY-MM-DD)", "entry", None),
        ]
        data = ask_form(self, "Issue Policy", fields)
        if not data:
            return
        if not query("SELECT 1 FROM customer WHERE customer_id=?", (data["Customer ID"],)):
            messagebox.showerror("Not found", "No such customer_id.")
            return
        if not is_positive_number(data["Sum insured"]):
            messagebox.showerror("Invalid input", "Sum insured must be a positive number.")
            return
        if not (is_valid_date(data["Start date (YYYY-MM-DD)"]) and is_valid_date(data["End date (YYYY-MM-DD)"])):
            messagebox.showerror("Invalid input", "Dates must be YYYY-MM-DD.")
            return
        plan_id = data["Plan"].split(" - ")[0]
        plan_row = query("SELECT premium_amount FROM plan_master WHERE plan_id=?", (plan_id,))[0]
        policy_number = next_number("POL")
        ok, policy_id, msg = execute(
            """INSERT INTO policy (policy_number, customer_id, plan_id, sum_insured, start_date, end_date, status, issued_by)
               VALUES (?,?,?,?,?,?, 'ACTIVE', ?)""",
            (policy_number, data["Customer ID"], plan_id, data["Sum insured"],
             data["Start date (YYYY-MM-DD)"], data["End date (YYYY-MM-DD)"], current_user["user_id"]),
        )
        if not ok:
            messagebox.showerror("Could not issue policy", msg)
            return
        execute_or_warn("INSERT INTO premium (policy_id, due_date, amount_due, status) VALUES (?,?,?, 'PENDING')",
                        (policy_id, data["Start date (YYYY-MM-DD)"], plan_row["premium_amount"]),
                        "Policy issued, but first premium could not be created")
        app_status(f"Policy issued: {policy_number} (policy_id={policy_id}).")
        self.refresh()

    def collect_premium(self):
        if not self.selected_policy_id:
            messagebox.showwarning("Select a policy", "Select a policy in the list first.")
            return
        dues = query("SELECT premium_id, due_date, amount_due FROM premium WHERE policy_id=? AND status IN ('PENDING','OVERDUE')",
                     (self.selected_policy_id,))
        if not dues:
            messagebox.showinfo("No dues", "No pending dues for this policy.")
            return
        choices = [f"{d['premium_id']} - due {d['due_date']} (₹{d['amount_due']})" for d in dues]
        fields = [
            ("Premium", "combo", choices),
            ("Amount paid", "entry", None),
            ("Payment mode", "combo", ["CASH", "CARD", "UPI", "NETBANKING", "CHEQUE"]),
        ]
        data = ask_form(self, "Collect Premium", fields)
        if not data:
            return
        if not is_positive_number(data["Amount paid"]):
            messagebox.showerror("Invalid input", "Amount must be a positive number.")
            return
        premium_id = data["Premium"].split(" - ")[0]
        ref = next_number("TXN")
        ok, _, msg = execute(
            "INSERT INTO payment (premium_id, payment_date, amount_paid, payment_mode, transaction_ref) VALUES (?,?,?,?,?)",
            (premium_id, str(date.today()), data["Amount paid"], data["Payment mode"], ref),
        )
        if ok:
            app_status(f"Payment recorded ({ref}); premium marked PAID.")
            self.on_select()
        else:
            messagebox.showerror("Could not record payment", msg)


# ======================================================================
# Tab: Claims (submit, verify, assess, decide, settle)
# ======================================================================
class ClaimsTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        left = tk.Frame(self, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(self, bg=BG)
        right.pack(side="right", fill="y")

        tk.Label(left, text="Claims", font=FONT_HEADER, bg=BG).pack(anchor="w")
        self.tree = ttk.Treeview(left)
        self.tree.pack(fill="both", expand=True, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        detail_frame = tk.Frame(left, bg=BG)
        detail_frame.pack(fill="x", pady=(10, 0))
        tk.Label(detail_frame, text="Treatment / Documents / Assessments / Decisions for selected claim",
                 font=FONT_HEADER, bg=BG).pack(anchor="w")
        self.detail_tree = ttk.Treeview(detail_frame, height=6)
        self.detail_tree.pack(fill="x", pady=6)

        tk.Button(right, text="+ Submit Claim", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.submit_claim).pack(fill="x", padx=10, pady=(0, 6))
        tk.Button(right, text="Verify Claim", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.verify_claim).pack(fill="x", padx=10, pady=6)
        tk.Button(right, text="Assess & Decide", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.assess_claim).pack(fill="x", padx=10, pady=6)
        tk.Button(right, text="Settle Claim", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.settle_claim).pack(fill="x", padx=10, pady=6)
        tk.Button(right, text="Refresh", padx=14, pady=6, command=self.refresh).pack(fill="x", padx=10, pady=(20, 6))

        self.selected_claim_id = None
        self.refresh()

    def refresh(self):
        rows = query("""SELECT cl.claim_id, cl.claim_number, p.policy_number,
                                c.first_name||' '||c.last_name AS holder, h.hospital_name,
                                cl.claim_date, cl.claimed_amount, cl.status
                         FROM claim cl JOIN policy p ON cl.policy_id=p.policy_id
                         JOIN customer c ON p.customer_id=c.customer_id
                         JOIN hospital h ON cl.hospital_id=h.hospital_id
                         ORDER BY cl.claim_id""")
        fill_tree(self.tree, rows)
        self.detail_tree.delete(*self.detail_tree.get_children())

    def on_select(self, _evt=None):
        cid = selected_value(self.tree, "claim_id")
        self.selected_claim_id = cid
        if cid:
            rows = query("""SELECT 'TREATMENT' AS type, treatment_name AS detail, treatment_cost AS amount FROM treatment WHERE claim_id=?
                             UNION ALL
                             SELECT 'DOCUMENT', document_type, NULL FROM claim_document WHERE claim_id=?
                             UNION ALL
                             SELECT 'ASSESSMENT', remarks, assessed_amount FROM assessment WHERE claim_id=?
                             UNION ALL
                             SELECT 'DECISION', decision_status, approved_amount FROM decision WHERE claim_id=?
                             UNION ALL
                             SELECT 'SETTLEMENT', settlement_mode, settled_amount FROM settlement WHERE claim_id=?""",
                          (cid, cid, cid, cid, cid))
            fill_tree(self.detail_tree, rows)

    def submit_claim(self):
        policies = query("SELECT policy_id, policy_number FROM policy WHERE status='ACTIVE'")
        hospitals = query("SELECT hospital_id, hospital_name FROM hospital")
        pol_choices = [f"{p['policy_id']} - {p['policy_number']}" for p in policies]
        hosp_choices = [f"{h['hospital_id']} - {h['hospital_name']}" for h in hospitals]
        fields = [
            ("Policy", "combo", pol_choices),
            ("Dependant ID (blank = policyholder)", "entry", None),
            ("Hospital", "combo", hosp_choices),
            ("Claim date (YYYY-MM-DD)", "entry", None),
            ("Claimed amount", "entry", None),
            ("Treatment name", "entry", None),
            ("Diagnosis", "entry", None),
            ("Admission date (YYYY-MM-DD)", "entry", None),
            ("Discharge date (YYYY-MM-DD)", "entry", None),
            ("Treatment cost", "entry", None),
        ]
        data = ask_form(self, "Submit Claim", fields)
        if not data:
            return
        for k in ("Claim date (YYYY-MM-DD)", "Admission date (YYYY-MM-DD)", "Discharge date (YYYY-MM-DD)"):
            if not is_valid_date(data[k]):
                messagebox.showerror("Invalid input", f"{k} must be YYYY-MM-DD.")
                return
        for k in ("Claimed amount", "Treatment cost"):
            if not is_positive_number(data[k]):
                messagebox.showerror("Invalid input", f"{k} must be a positive number.")
                return
        policy_id = data["Policy"].split(" - ")[0]
        hospital_id = data["Hospital"].split(" - ")[0]
        dependant_id = data["Dependant ID (blank = policyholder)"] or None
        claim_number = next_number("CLM")
        ok, claim_id, msg = execute(
            """INSERT INTO claim (claim_number, policy_id, dependant_id, hospital_id, claim_date,
               claimed_amount, status, submitted_by) VALUES (?,?,?,?,?,?, 'SUBMITTED', ?)""",
            (claim_number, policy_id, dependant_id, hospital_id, data["Claim date (YYYY-MM-DD)"],
             data["Claimed amount"], current_user["user_id"]),
        )
        if not ok:
            messagebox.showerror("Claim rejected by business rule", msg)
            app_status("Claim submission blocked by a business rule.", ok=False)
            return
        execute_or_warn(
            """INSERT INTO treatment (claim_id, treatment_name, diagnosis, admission_date, discharge_date, treatment_cost)
               VALUES (?,?,?,?,?,?)""",
            (claim_id, data["Treatment name"], data["Diagnosis"], data["Admission date (YYYY-MM-DD)"],
             data["Discharge date (YYYY-MM-DD)"], data["Treatment cost"]),
            "Claim saved, but treatment details were rejected",
        )
        app_status(f"Claim submitted: {claim_number} (claim_id={claim_id}).")
        self.refresh()

    def verify_claim(self):
        if not self.selected_claim_id:
            messagebox.showwarning("Select a claim", "Select a claim in the list first.")
            return
        fields = [
            ("Attach a document?", "combo", ["N", "Y"]),
            ("Document type", "combo", ["PRESCRIPTION", "DISCHARGE_SUMMARY", "BILL", "LAB_REPORT", "ID_PROOF", "OTHER"]),
            ("File reference", "entry", None),
        ]
        data = ask_form(self, "Verify Claim", fields)
        if not data:
            return
        if data["Attach a document?"] == "Y" and data["File reference"]:
            execute_or_warn("INSERT INTO claim_document (claim_id, document_type, file_reference, upload_date) VALUES (?,?,?,?)",
                            (self.selected_claim_id, data["Document type"], data["File reference"], str(date.today())))
        if not execute_or_warn("UPDATE claim SET status='VERIFIED' WHERE claim_id=?", (self.selected_claim_id,)):
            return
        app_status(f"Claim {self.selected_claim_id} marked VERIFIED.")
        self.refresh()

    def assess_claim(self):
        if not self.selected_claim_id:
            messagebox.showwarning("Select a claim", "Select a claim in the list first.")
            return
        fields = [
            ("Assessed amount", "entry", None),
            ("Remarks", "entry", None),
            ("Record decision now?", "combo", ["Y", "N"]),
            ("Decision", "combo", ["APPROVED", "REJECTED", "PARTIALLY_APPROVED"]),
            ("Approved amount", "entry", None),
        ]
        data = ask_form(self, "Assess Claim", fields)
        if not data:
            return
        if not is_positive_number(data["Assessed amount"]):
            messagebox.showerror("Invalid input", "Assessed amount must be a positive number.")
            return
        if not execute_or_warn("UPDATE claim SET status='UNDER_ASSESSMENT' WHERE claim_id=?", (self.selected_claim_id,)):
            return
        if not execute_or_warn(
            "INSERT INTO assessment (claim_id, assessor_id, assessment_date, assessed_amount, remarks) VALUES (?,?,?,?,?)",
            (self.selected_claim_id, current_user["user_id"], str(date.today()), data["Assessed amount"], data["Remarks"]),
        ):
            return
        if data["Record decision now?"] == "Y":
            approved = 0
            if data["Decision"] != "REJECTED":
                if not is_positive_number(data["Approved amount"]):
                    messagebox.showerror("Invalid input", "Approved amount must be a positive number.")
                    return
                approved = data["Approved amount"]
            ok, _, msg = execute(
                "INSERT INTO decision (claim_id, decision_date, decision_status, approved_amount, decided_by) VALUES (?,?,?,?,?)",
                (self.selected_claim_id, str(date.today()), data["Decision"], approved, current_user["user_id"]),
            )
            if not ok:
                messagebox.showerror("Could not record decision", msg)
        app_status(f"Assessment recorded for claim {self.selected_claim_id}.")
        self.refresh()

    def settle_claim(self):
        if not self.selected_claim_id:
            messagebox.showwarning("Select a claim", "Select a claim in the list first.")
            return
        claim = query("SELECT status FROM claim WHERE claim_id=?", (self.selected_claim_id,))[0]
        if claim["status"] != "APPROVED":
            messagebox.showwarning("Not approved", f"Claim status is {claim['status']}; only APPROVED claims can be settled.")
            return
        fields = [
            ("Settled amount", "entry", None),
            ("Settlement mode", "combo", ["NEFT", "CHEQUE", "UPI"]),
        ]
        data = ask_form(self, "Settle Claim", fields)
        if not data:
            return
        if not is_positive_number(data["Settled amount"]):
            messagebox.showerror("Invalid input", "Settled amount must be a positive number.")
            return
        ref = next_number("SETL")
        ok, _, msg = execute(
            "INSERT INTO settlement (claim_id, settlement_date, settled_amount, settlement_mode, transaction_ref) VALUES (?,?,?,?,?)",
            (self.selected_claim_id, str(date.today()), data["Settled amount"], data["Settlement mode"], ref),
        )
        if ok:
            app_status(f"Settlement recorded ({ref}); claim marked SETTLED.")
            self.refresh()
        else:
            messagebox.showerror("Settlement rejected by business rule", msg)
            app_status("Settlement blocked by a business rule.", ok=False)


# ======================================================================
# Tab: Appeals
# ======================================================================
class AppealsTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        left = tk.Frame(self, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(self, bg=BG)
        right.pack(side="right", fill="y")

        tk.Label(left, text="Appeals", font=FONT_HEADER, bg=BG).pack(anchor="w")
        self.tree = ttk.Treeview(left)
        self.tree.pack(fill="both", expand=True, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        tk.Button(right, text="+ File Appeal", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.file_appeal).pack(fill="x", padx=10, pady=(0, 8))
        tk.Button(right, text="Resolve Appeal", bg=ACCENT, fg="white", padx=14, pady=6,
                  command=self.resolve_appeal).pack(fill="x", padx=10, pady=8)
        tk.Button(right, text="Refresh", padx=14, pady=6, command=self.refresh).pack(fill="x", padx=10, pady=8)

        self.selected_appeal_id = None
        self.refresh()

    def refresh(self):
        rows = query("""SELECT a.appeal_id, cl.claim_number, c.first_name||' '||c.last_name AS holder,
                                a.appeal_date, a.reason, a.appeal_status, a.resolution_date
                         FROM appeal a JOIN claim cl ON a.claim_id=cl.claim_id
                         JOIN policy p ON cl.policy_id=p.policy_id
                         JOIN customer c ON p.customer_id=c.customer_id ORDER BY a.appeal_id""")
        fill_tree(self.tree, rows)

    def on_select(self, _evt=None):
        self.selected_appeal_id = selected_value(self.tree, "appeal_id")

    def file_appeal(self):
        claims = query("SELECT claim_id, claim_number, status FROM claim WHERE status IN ('APPROVED','REJECTED','SETTLED')")
        choices = [f"{c['claim_id']} - {c['claim_number']} ({c['status']})" for c in claims]
        if not choices:
            messagebox.showinfo("No eligible claims", "No decided claims available to appeal.")
            return
        fields = [("Claim", "combo", choices), ("Reason", "entry", None)]
        data = ask_form(self, "File Appeal", fields)
        if not data or not data["Reason"]:
            return
        claim_id = data["Claim"].split(" - ")[0]
        if not execute_or_warn("INSERT INTO appeal (claim_id, appeal_date, reason, appeal_status) VALUES (?,?,?, 'PENDING')",
                               (claim_id, str(date.today()), data["Reason"])):
            return
        app_status("Appeal filed; claim marked APPEALED.")
        self.refresh()

    def resolve_appeal(self):
        if not self.selected_appeal_id:
            messagebox.showwarning("Select an appeal", "Select an appeal in the list first.")
            return
        fields = [("Resolution", "combo", ["RESOLVED", "REJECTED"]), ("Remarks", "entry", None)]
        data = ask_form(self, "Resolve Appeal", fields)
        if not data:
            return
        if not execute_or_warn("UPDATE appeal SET appeal_status=?, resolution_date=?, resolution_remarks=? WHERE appeal_id=?",
                               (data["Resolution"], str(date.today()), data["Remarks"], self.selected_appeal_id)):
            return
        app_status("Appeal updated.")
        self.refresh()


# ======================================================================
# Tab: Reports
# ======================================================================
REPORTS = {
    "Active Policies": "SELECT * FROM vw_active_policies",
    "Premium Dues": "SELECT * FROM vw_premium_dues",
    "Pending Claims": "SELECT * FROM vw_pending_claims",
    "Claim Approval Rate": "SELECT * FROM vw_claim_approval_rate",
    "Settlement Report": "SELECT * FROM vw_settlement_report",
    "Hospital-wise Claims": "SELECT * FROM vw_hospital_claims",
    "Appeals Report": "SELECT * FROM vw_appeals_report",
}


class ReportsTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(0, 8))
        tk.Label(top, text="Report:", font=FONT_NORMAL, bg=BG).pack(side="left")
        self.choice = tk.StringVar(value=list(REPORTS.keys())[0])
        ttk.Combobox(top, textvariable=self.choice, values=list(REPORTS.keys()),
                     state="readonly", width=30).pack(side="left", padx=8)
        tk.Button(top, text="Run Report", bg=ACCENT, fg="white", command=self.run).pack(side="left", padx=8)

        self.tree = ttk.Treeview(self)
        self.tree.pack(fill="both", expand=True)
        self.run()

    def run(self):
        sql = REPORTS[self.choice.get()]
        rows = query(sql)
        fill_tree(self.tree, rows)
        app_status(f"Report '{self.choice.get()}' - {len(rows)} row(s).")


def main():
    if "--reset" in sys.argv:
        try:
            db.build_fresh_database()
        except (db.DatabaseConfigError,) + db.DB_ERRORS as e:
            print("Reset failed:", e)
    ok, msg = db.test_connection()
    if not ok:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("HIPCMS - cannot reach the database",
                             f"{db.describe_connection()}\n\n{msg}\n\n"
                             "Check app/db_config.ini, make sure MySQL is running, then run\n"
                             "    python setup_database.py")
        root.destroy()
        print(msg)
        return 1
    print(f"Database: {db.describe_connection()}  ->  {msg}")
    LoginWindow().mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
