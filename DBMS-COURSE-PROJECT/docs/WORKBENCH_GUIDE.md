# Running HIPCMS in MySQL Workbench

The three scripts in `sql/` are plain MySQL 8.0 SQL — they have been tested
end-to-end against a real MySQL 8.0 server (schema, triggers, sample data,
and every report/query all execute cleanly with no errors). MySQL Workbench
is just a GUI over the same server, so opening and running them there works
exactly the same way. This guide walks through doing that.

## 1. Prerequisites

- MySQL Server 8.0+ installed and running (locally or remote).
- MySQL Workbench installed (Database → Connect to Database will detect a
  local server automatically in most installs).

## 2. Connect to your server

1. Open MySQL Workbench.
2. On the home screen, click the **+** next to "MySQL Connections".
3. Connection name: `HIPCMS Local` (or anything you like).
4. Hostname: `127.0.0.1`, Port: `3306`, Username: `root` (or your own user).
5. Click **Test Connection**, enter the password if prompted, then **OK**.
6. Double-click the new connection tile to open a SQL editor tab.

## 3. Run the three scripts, in order

For each file below: **File → Open SQL Script...** → select the file →
click the **lightning bolt (⚡ Execute)** icon (or Ctrl+Shift+Enter to run
the whole script) → watch the **Output** panel at the bottom for green
checkmarks (success) or red X's (error).

1. `sql/01_schema_mysql.sql`
   Creates the `hipcms` database, all 15 tables with PK/FK/UNIQUE/CHECK/
   DEFAULT constraints, indexes, and the 9 business-rule triggers.
   After running, refresh the **SCHEMAS** panel on the left (the small
   refresh icon) — `hipcms` should appear with its tables underneath.

2. `sql/02_sample_data.sql`
   Populates all tables with the realistic sample dataset. Run this only
   after step 1 succeeds.

3. `sql/03_queries_and_views.sql`
   Creates the 7 report views (`vw_active_policies`, `vw_premium_dues`,
   `vw_pending_claims`, `vw_claim_approval_rate`, `vw_settlement_report`,
   `vw_hospital_claims`, `vw_appeals_report`) and runs the additional
   join/subquery/aggregate example queries. Each `SELECT` in the script
   produces its own result grid in Workbench's **Result Grid** area at the
   bottom — click through the numbered result tabs to see each report's
   output.

## 4. Browse data and re-run individual reports

- **Left sidebar → SCHEMAS → hipcms → Tables** — right-click any table →
  **Select Rows - Limit 1000** to browse its data in a grid.
- **Left sidebar → SCHEMAS → hipcms → Views** — same right-click →
  **Select Rows** on any `vw_...` view to re-run that report on demand,
  e.g. `vw_pending_claims` or `vw_claim_approval_rate`.
- To run one query ad hoc, type it in a new SQL tab and press
  Ctrl+Enter with the cursor on that line (runs just the current
  statement rather than the whole script).

## 5. Generate the ER diagram directly from the live schema (optional)

MySQL Workbench can reverse-engineer an EER diagram straight from the
database, which is a useful alternative to (or cross-check against) the
`diagrams/hipcms_er_diagram.png` already included in this project:

1. **Database → Reverse Engineer...**
2. Pick the `HIPCMS Local` connection → Next.
3. Select the `hipcms` schema → Next → Execute → Finish.
4. Workbench lays out an EER diagram of all 15 tables with their
   relationships (crow's-foot notation), which you can drag into a
   readable layout and export via **File → Export → Export as PNG...**.

## 6. Testing the business-rule triggers directly in Workbench

Open a new SQL tab against the `hipcms` schema and run each of these one
at a time — every one should fail with the stated error, proving the rule
is enforced by the database itself, not just the application:

```sql
-- Duplicate claim (same policy/hospital/date as an existing one)
INSERT INTO claim (claim_number, policy_id, hospital_id, claim_date, claimed_amount, status)
VALUES ('CLM-TEST-1',1,1,'2025-03-10',5000,'SUBMITTED');
-- Expect: Duplicate claim: an identical claim already exists...

-- Claim against an inactive (EXPIRED) policy
INSERT INTO claim (claim_number, policy_id, hospital_id, claim_date, claimed_amount, status)
VALUES ('CLM-TEST-2',3,1,'2025-01-01',5000,'SUBMITTED');
-- Expect: Claim rejected: policy is not ACTIVE

-- Claim date outside the policy's validity window
INSERT INTO claim (claim_number, policy_id, hospital_id, claim_date, claimed_amount, status)
VALUES ('CLM-TEST-3',1,1,'2026-05-01',5000,'SUBMITTED');
-- Expect: Claim rejected: claim date is outside policy validity period

-- Settlement exceeding the policy's sum insured
INSERT INTO settlement (claim_id, settlement_date, settled_amount, settlement_mode, transaction_ref)
VALUES (1,'2025-03-20',5000000,'NEFT','TXN-X1');
-- Expect: Settlement exceeds policy sum insured

-- Settlement exceeding the approved decision amount
INSERT INTO settlement (claim_id, settlement_date, settled_amount, settlement_mode, transaction_ref)
VALUES (1,'2025-03-20',95000,'NEFT','TXN-X2');
-- Expect: Settlement exceeds the approved decision amount

-- Customer date of birth not in the past
INSERT INTO customer (first_name,last_name,dob,gender,id_proof_number,phone,email,address_line,city,state,pincode)
VALUES ('Future','Person','2099-01-01','M','IDFUTURE','9999999999','future@example.com','x','x','x','000000');
-- Expect: Customer date of birth must be in the past
```

All six were run against a live MySQL 8.0 instance while building this
project and confirmed to raise exactly these errors (see section 3.5 of
`docs/Project_Report.docx`).

## 6b. A note on the dob CHECK constraint

MySQL 8.0 does not allow non-deterministic functions like `CURDATE()`
inside a `CHECK` constraint (`ERROR 3814`), so "date of birth must be in
the past" is enforced by the trigger `trg_customer_dob_past` instead of a
`CHECK` clause. This was caught by actually running the script on MySQL
Workbench's underlying server, not assumed from a syntax read — that's
also why this guide recommends running the scripts for real rather than
just eyeballing them.

## 7. The Python application already uses this MySQL database

The GUI (`app/gui_app.py`) and console app (`app/app.py`) connect to the
same `hipcms` database you see in Workbench. Settings are in
`app/db_config.ini`:

```ini
[database]
backend  = mysql
host     = 127.0.0.1
port     = 3306
user     = root
password = <your MySQL password>
database = hipcms
```

Then:

```bash
cd app
pip install -r requirements.txt     # mysql-connector-python
python setup_database.py            # (optional) rebuild hipcms from the 3 scripts
python gui_app.py
```

`setup_database.py` runs exactly the same three scripts as section 3, so
you can create the database either from Workbench or from this command.

## 8. Watching UI changes appear in Workbench

Keep Workbench open next to the application. After inserting or deleting a
record in the **Database Records** tab, re-run in Workbench:

```sql
SELECT COUNT(*) FROM hipcms.customer;
SELECT * FROM hipcms.customer ORDER BY customer_id DESC LIMIT 5;
```

The new row appears (or disappears) immediately, because the application
commits each change. Workbench's result grid caches results, so press
**Ctrl+Enter** again (or the refresh icon on the grid) to re-query. The full
demonstration script is in `docs/UI_DEMO_GUIDE.md`.
