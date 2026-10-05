# UI Demonstration Guide — Insert / Delete / View on MySQL

This is the script for the **User Interface (5 marks)** evaluation:
*a working UI connected to the MySQL database that supports insertion,
deletion and viewing of records, with each change shown in the database.*

Total time: about 5 minutes.

---

## 0. Before the evaluator arrives (one-time setup)

1. MySQL Server 8.0 is running.
2. Edit `app/db_config.ini` → set `user` and `password` for your MySQL.
3. In a terminal:

   ```bash
   cd app
   pip install -r requirements.txt
   python setup_database.py --yes      # fresh hipcms database with sample data
   python gui_app.py
   ```

   The terminal prints e.g.
   `Database: MySQL root@127.0.0.1:3306 / hipcms -> MySQL 8.0.x - connected (15 customers)`

4. Open **MySQL Workbench**, connect, open a SQL tab and type:

   ```sql
   USE hipcms;
   SELECT COUNT(*) FROM customer;
   SELECT customer_id, first_name, last_name, city FROM customer ORDER BY customer_id DESC LIMIT 5;
   ```

5. Arrange the HIPCMS window and Workbench side by side.

If MySQL is not reachable, the app shows a dialog telling you exactly what is
wrong (server not running / wrong password / database not created).

---

## 1. Show the connection (15 s)

- Log in as **admin** / **password**.
- Point to the status bar, bottom-right: **DB: MySQL root@127.0.0.1:3306 / hipcms**.
- Point to the SQL activity log: first line is *Connected to MySQL ...*.

> "The UI is connected to the hipcms database on MySQL. Every statement it
> sends appears in this log."

## 2. VIEW records (45 s)

- On the **Database Records** tab, table `customer` is already selected.
- Click **View Records**. Log shows
  `SELECT * FROM customer ORDER BY customer_id;  -> 15 row(s) returned`.
- Top-right label: **15 row(s) in `customer`**.
- In Workbench run `SELECT COUNT(*) FROM customer;` → **15**. Same data.
- Change the table drop-down to `policy` or `claim` to show any table can be viewed.

## 3. INSERT a record (1.5 min)

- Switch back to `customer`, click **+ Insert Record**.
- Point out: fields marked `*` are required, `gender` is a drop-down from
  the CHECK constraint, `customer_id` / `created_at` are filled by MySQL.
- Enter, for example:

  | Field | Value |
  |---|---|
  | first_name | Ananya |
  | last_name | Rao |
  | dob | 1996-04-12 |
  | gender | F |
  | id_proof_number | AADH-9988-7766 |
  | phone | 9876543210 |
  | email | ananya.rao@example.com |
  | address_line | 12 MG Road |
  | city / state / pincode | Hyderabad / Telangana / 500001 |

- Click **INSERT**. Show:
  - the new row highlighted at the bottom of the grid (`customer_id = 16`),
  - log: `INSERT INTO customer (...) VALUES (...);`
    `-> 1 row inserted, customer_id = 16 | COUNT(*) 15 -> 16 (COMMIT done)`.
- **In Workbench** re-run both queries → count **16**, Ananya Rao is listed.
- Optional: click **Verify in DB** → re-reads the row through a new
  connection: `-> FOUND: customer_id=16, first_name=Ananya ...`.

*Optional constraint demo (20 s):* click **+ Insert Record** again and use
the same email → MySQL rejects it: *Duplicate value – UNIQUE constraint*
(error 1062). Nothing is inserted; count stays 16.

*Optional FK demo:* choose table `dependant` → **+ Insert Record** →
`customer_id` is a drop-down of existing customers (pick 16 – Ananya Rao).

## 4. DELETE a record (1.5 min)

- Table `customer`, click the row **customer_id 16**, click **Delete Selected**.
- The confirmation shows the exact statement
  `DELETE FROM customer WHERE customer_id = 16;` and any related rows.
  (If you added a dependant for 16 it says it will be removed by CASCADE.)
- Click **Yes**. Log: `-> 1 row(s) deleted | COUNT(*) 16 -> 15 (COMMIT done)`.
- **In Workbench** re-run → count **15**, Ananya Rao is gone.
- Click **Verify in DB** → `-> 0 rows: record does not exist in the database`.

*Referential-integrity demo (30 s):* select **customer_id 1** and click
**Delete Selected**. The confirmation warns that 1 policy references this
customer with **RESTRICT**. Click Yes → MySQL refuses (error 1451) and the
row stays. This shows the database, not the UI, is protecting integrity.

## 5. (If asked) The business screens

The other tabs use the same live database: add/delete customers and
dependants, issue policies, collect premiums, submit → verify → assess →
settle claims, appeals, and the seven report views.

---

## Questions you may be asked

**Where is the connection code?** `app/db.py` → `get_connection()` uses
`mysql.connector.connect(...)` with the values from `db_config.ini`.

**How is SQL injection prevented?** Values are always passed as parameters
(`?` → `%s` placeholders), never concatenated into the SQL string. Table and
column names in the Database Records screen come only from MySQL's own
`information_schema`, not from user typing.

**How does the insert form know the columns?** It queries
`information_schema.COLUMNS`, `KEY_COLUMN_USAGE` (foreign keys) and
`CHECK_CONSTRAINTS` (allowed values) for the chosen table.

**Why can only admin delete?** Deletion is a privileged operation; agents
and assessors can view and insert but not delete.

**Is the change really saved?** Yes – each statement is followed by
`COMMIT`; "Verify in DB" and Workbench both read it through a separate
connection.
