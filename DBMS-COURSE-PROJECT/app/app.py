"""
HIPCMS - Health Insurance Policy and Claims Management System
Console front-end (Review 3 deliverable)

Run:
    python3 app.py            # normal interactive use
    python3 app.py --reset    # wipe and rebuild the demo database first

Connects to the MySQL database configured in db_config.ini (see db.py).
Create it first with:  python setup_database.py
"""
import sys
import hashlib
from datetime import date

import db
from validators import (
    prompt, prompt_choice, is_valid_email, is_valid_phone,
    is_valid_date, is_positive_number, is_non_empty,
)

current_user = None  # set at login


# ----------------------------------------------------------------------
# Auth
# ----------------------------------------------------------------------
def hash_pw(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def login():
    global current_user
    print("\n=== HIPCMS LOGIN ===")
    print("(demo accounts: admin/agent1/agent2/assessor1/assessor2, password: 'password')")
    for _ in range(3):
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        conn = db.get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND is_active = 1", (username,)
        ).fetchone()
        conn.close()
        # NOTE: demo seed data stores a placeholder hash; accept the fixed
        # demo password 'password' for any seeded account for ease of testing.
        if row and (hash_pw(password) == row["password_hash"] or password == "password"):
            current_user = dict(row)
            print(f"Welcome, {current_user['full_name']} ({current_user['role']})\n")
            return True
        print("Invalid credentials. Try again.\n")
    return False


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def print_rows(rows, headers=None):
    if not rows:
        print("  (no records found)")
        return
    if headers is None:
        headers = rows[0].keys()
    widths = [max(len(str(h)), *(len(str(r[h])) for r in rows)) for h in headers]
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    print(header_line)
    print("-" * len(header_line))
    for r in rows:
        print(" | ".join(str(r[h]).ljust(w) for h, w in zip(headers, widths)))


def next_number(prefix, year=None):
    year = year or date.today().year
    return f"{prefix}-{year}-{str(__import__('random').randint(1000,9999))}"


# ----------------------------------------------------------------------
# 1. Customer & Dependant entry
# ----------------------------------------------------------------------
def add_customer():
    print("\n-- New Customer --")
    conn = db.get_connection()
    try:
        first = prompt("First name: ", is_non_empty, "First name is required")
        last = prompt("Last name: ", is_non_empty, "Last name is required")
        dob = prompt("DOB (YYYY-MM-DD): ", is_valid_date, "Enter a valid date YYYY-MM-DD")
        gender = prompt_choice("Gender", ["M", "F", "O"])
        idproof = prompt("ID proof number: ", is_non_empty, "ID proof is required")
        phone = prompt("Phone (10 digits): ", is_valid_phone, "Enter a valid 10-digit phone number")
        email = prompt("Email: ", is_valid_email, "Enter a valid email")
        address = prompt("Address line: ", is_non_empty, "Address is required")
        city = prompt("City: ", is_non_empty, "City is required")
        state = prompt("State: ", is_non_empty, "State is required")
        pincode = prompt("Pincode: ", is_non_empty, "Pincode is required")
        cur = conn.execute(
            """INSERT INTO customer (first_name,last_name,dob,gender,id_proof_number,
               phone,email,address_line,city,state,pincode)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (first, last, dob, gender, idproof, phone, email, address, city, state, pincode),
        )
        conn.commit()
        print(f"Customer created with customer_id = {cur.lastrowid}")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! Could not create customer: {e}")
    finally:
        conn.close()


def add_dependant():
    print("\n-- Add Dependant --")
    conn = db.get_connection()
    try:
        cust_id = prompt("Customer ID: ", is_non_empty)
        cust = conn.execute("SELECT * FROM customer WHERE customer_id=?", (cust_id,)).fetchone()
        if not cust:
            print("  ! No such customer.")
            return
        first = prompt("Dependant first name: ", is_non_empty)
        last = prompt("Dependant last name: ", is_non_empty)
        dob = prompt("DOB (YYYY-MM-DD): ", is_valid_date)
        gender = prompt_choice("Gender", ["M", "F", "O"])
        rel = prompt_choice("Relationship", ["SPOUSE", "SON", "DAUGHTER", "FATHER", "MOTHER", "OTHER"])
        cur = conn.execute(
            """INSERT INTO dependant (customer_id, first_name, last_name, dob, gender, relationship)
               VALUES (?,?,?,?,?,?)""",
            (cust_id, first, last, dob, gender, rel),
        )
        conn.commit()
        print(f"Dependant added with dependant_id = {cur.lastrowid}")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! Could not add dependant: {e}")
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 2. Policy issue
# ----------------------------------------------------------------------
def issue_policy():
    print("\n-- Issue Policy --")
    conn = db.get_connection()
    try:
        print("Available plans:")
        print_rows(conn.execute("SELECT plan_id, plan_name, plan_type, coverage_amount, premium_amount FROM plan_master WHERE is_active=1").fetchall())
        cust_id = prompt("\nCustomer ID: ", is_non_empty)
        if not conn.execute("SELECT 1 FROM customer WHERE customer_id=?", (cust_id,)).fetchone():
            print("  ! No such customer. Create the customer first (menu option 1).")
            return
        plan_id = prompt("Plan ID: ", is_non_empty)
        plan = conn.execute("SELECT * FROM plan_master WHERE plan_id=?", (plan_id,)).fetchone()
        if not plan:
            print("  ! No such plan.")
            return
        sum_insured = prompt(f"Sum insured (suggested {plan['coverage_amount']}): ", is_positive_number)
        start_date = prompt("Start date (YYYY-MM-DD): ", is_valid_date)
        end_date = prompt("End date (YYYY-MM-DD): ", is_valid_date)
        policy_number = next_number("POL")
        cur = conn.execute(
            """INSERT INTO policy (policy_number, customer_id, plan_id, sum_insured,
               start_date, end_date, status, issued_by)
               VALUES (?,?,?,?,?,?, 'ACTIVE', ?)""",
            (policy_number, cust_id, plan_id, sum_insured, start_date, end_date, current_user["user_id"]),
        )
        policy_id = cur.lastrowid
        conn.execute(
            "INSERT INTO premium (policy_id, due_date, amount_due, status) VALUES (?,?,?, 'PENDING')",
            (policy_id, start_date, plan["premium_amount"]),
        )
        conn.commit()
        print(f"Policy issued: {policy_number} (policy_id={policy_id}); first premium installment scheduled.")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! Could not issue policy: {e}")
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 3. Premium collection
# ----------------------------------------------------------------------
def collect_premium():
    print("\n-- Premium Collection --")
    conn = db.get_connection()
    try:
        policy_id = prompt("Policy ID: ", is_non_empty)
        dues = conn.execute(
            "SELECT * FROM premium WHERE policy_id=? AND status IN ('PENDING','OVERDUE')", (policy_id,)
        ).fetchall()
        if not dues:
            print("  No pending dues for this policy.")
            return
        print_rows(dues)
        premium_id = prompt("\nPremium ID to pay: ", is_non_empty)
        premium = conn.execute("SELECT * FROM premium WHERE premium_id=?", (premium_id,)).fetchone()
        if not premium:
            print("  ! No such premium record.")
            return
        amount = prompt(f"Amount paid (due {premium['amount_due']}): ", is_positive_number)
        mode = prompt_choice("Payment mode", ["CASH", "CARD", "UPI", "NETBANKING", "CHEQUE"])
        ref = next_number("TXN")
        conn.execute(
            """INSERT INTO payment (premium_id, payment_date, amount_paid, payment_mode, transaction_ref)
               VALUES (?,?,?,?,?)""",
            (premium_id, str(date.today()), amount, mode, ref),
        )
        conn.commit()
        print(f"Payment recorded ({ref}); premium marked PAID.")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! Could not record payment: {e}")
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 4. Claim submission, verification, treatment & documents
# ----------------------------------------------------------------------
def submit_claim():
    print("\n-- Submit Claim --")
    conn = db.get_connection()
    try:
        policy_id = prompt("Policy ID: ", is_non_empty)
        policy = conn.execute("SELECT * FROM policy WHERE policy_id=?", (policy_id,)).fetchone()
        if not policy:
            print("  ! No such policy.")
            return
        dep_input = prompt("Dependant ID (blank if claim is for the policyholder): ", allow_blank=True)
        dependant_id = dep_input if dep_input else None
        print("Hospitals:")
        print_rows(conn.execute("SELECT hospital_id, hospital_name, city, network_type FROM hospital").fetchall())
        hospital_id = prompt("\nHospital ID: ", is_non_empty)
        claim_date = prompt("Claim date (YYYY-MM-DD): ", is_valid_date)
        claimed_amount = prompt("Claimed amount: ", is_positive_number)
        claim_number = next_number("CLM")
        cur = conn.execute(
            """INSERT INTO claim (claim_number, policy_id, dependant_id, hospital_id,
               claim_date, claimed_amount, status, submitted_by)
               VALUES (?,?,?,?,?,?, 'SUBMITTED', ?)""",
            (claim_number, policy_id, dependant_id, hospital_id, claim_date, claimed_amount, current_user["user_id"]),
        )
        claim_id = cur.lastrowid

        print("\nEnter treatment details for this claim:")
        tname = prompt("Treatment name: ", is_non_empty)
        diagnosis = prompt("Diagnosis: ", is_non_empty)
        adm = prompt("Admission date (YYYY-MM-DD): ", is_valid_date)
        dis = prompt("Discharge date (YYYY-MM-DD): ", is_valid_date)
        cost = prompt("Treatment cost: ", is_positive_number)
        conn.execute(
            """INSERT INTO treatment (claim_id, treatment_name, diagnosis, admission_date,
               discharge_date, treatment_cost) VALUES (?,?,?,?,?,?)""",
            (claim_id, tname, diagnosis, adm, dis, cost),
        )
        conn.commit()
        print(f"\nClaim submitted: {claim_number} (claim_id={claim_id}), status=SUBMITTED")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        conn.rollback()
        print(f"  ! Claim rejected by business rule check: {e}")
    finally:
        conn.close()


def verify_claim():
    print("\n-- Claim Verification (attach documents, mark VERIFIED) --")
    conn = db.get_connection()
    try:
        claim_id = prompt("Claim ID: ", is_non_empty)
        claim = conn.execute("SELECT * FROM claim WHERE claim_id=?", (claim_id,)).fetchone()
        if not claim:
            print("  ! No such claim.")
            return
        add_doc = prompt_choice("Attach a document now?", ["Y", "N"])
        if add_doc == "Y":
            dtype = prompt_choice("Document type", ["PRESCRIPTION", "DISCHARGE_SUMMARY", "BILL", "LAB_REPORT", "ID_PROOF", "OTHER"])
            ref = prompt("File reference/path: ", is_non_empty)
            conn.execute(
                "INSERT INTO claim_document (claim_id, document_type, file_reference, upload_date) VALUES (?,?,?,?)",
                (claim_id, dtype, ref, str(date.today())),
            )
        conn.execute("UPDATE claim SET status='VERIFIED' WHERE claim_id=?", (claim_id,))
        conn.commit()
        print(f"Claim {claim['claim_number']} marked VERIFIED.")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! {e}")
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 5. Assessment & Decision
# ----------------------------------------------------------------------
def assess_claim():
    print("\n-- Claim Assessment --")
    conn = db.get_connection()
    try:
        claim_id = prompt("Claim ID: ", is_non_empty)
        claim = conn.execute("SELECT * FROM claim WHERE claim_id=?", (claim_id,)).fetchone()
        if not claim:
            print("  ! No such claim.")
            return
        conn.execute("UPDATE claim SET status='UNDER_ASSESSMENT' WHERE claim_id=?", (claim_id,))
        assessed_amount = prompt("Assessed amount: ", is_positive_number)
        remarks = prompt("Remarks: ", allow_blank=True)
        conn.execute(
            """INSERT INTO assessment (claim_id, assessor_id, assessment_date, assessed_amount, remarks)
               VALUES (?,?,?,?,?)""",
            (claim_id, current_user["user_id"], str(date.today()), assessed_amount, remarks),
        )
        conn.commit()
        print(f"Assessment recorded for claim {claim['claim_number']}.")

        record_decision = prompt_choice("Record a decision now?", ["Y", "N"])
        if record_decision == "Y":
            status = prompt_choice("Decision", ["APPROVED", "REJECTED", "PARTIALLY_APPROVED"])
            approved_amount = 0
            if status != "REJECTED":
                approved_amount = prompt("Approved amount: ", is_positive_number)
            conn.execute(
                """INSERT INTO decision (claim_id, decision_date, decision_status, approved_amount, decided_by)
                   VALUES (?,?,?,?,?)""",
                (claim_id, str(date.today()), status, approved_amount, current_user["user_id"]),
            )
            conn.commit()
            print(f"Decision recorded: {status}. Claim status updated automatically.")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! {e}")
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 6. Settlement
# ----------------------------------------------------------------------
def settle_claim():
    print("\n-- Settlement --")
    conn = db.get_connection()
    try:
        claim_id = prompt("Claim ID (must be APPROVED): ", is_non_empty)
        claim = conn.execute("SELECT * FROM claim WHERE claim_id=?", (claim_id,)).fetchone()
        if not claim:
            print("  ! No such claim.")
            return
        if claim["status"] != "APPROVED":
            print(f"  ! Claim status is {claim['status']}; only APPROVED claims can be settled.")
            return
        decision = conn.execute(
            "SELECT * FROM decision WHERE claim_id=? ORDER BY decision_id DESC LIMIT 1", (claim_id,)
        ).fetchone()
        settled_amount = prompt(f"Settlement amount (approved {decision['approved_amount']}): ", is_positive_number)
        mode = prompt_choice("Settlement mode", ["NEFT", "CHEQUE", "UPI"])
        ref = next_number("SETL")
        conn.execute(
            """INSERT INTO settlement (claim_id, settlement_date, settled_amount, settlement_mode, transaction_ref)
               VALUES (?,?,?,?,?)""",
            (claim_id, str(date.today()), settled_amount, mode, ref),
        )
        conn.commit()
        print(f"Settlement recorded ({ref}); claim marked SETTLED.")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! Settlement rejected by business rule check: {e}")
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 7. Appeal
# ----------------------------------------------------------------------
def file_appeal():
    print("\n-- File Appeal --")
    conn = db.get_connection()
    try:
        claim_id = prompt("Claim ID: ", is_non_empty)
        claim = conn.execute("SELECT * FROM claim WHERE claim_id=?", (claim_id,)).fetchone()
        if not claim:
            print("  ! No such claim.")
            return
        if claim["status"] not in ("REJECTED", "APPROVED", "SETTLED"):
            print(f"  ! Appeals can only be filed on decided claims (current status: {claim['status']}).")
            return
        reason = prompt("Reason for appeal: ", is_non_empty)
        conn.execute(
            """INSERT INTO appeal (claim_id, appeal_date, reason, appeal_status)
               VALUES (?,?,?, 'PENDING')""",
            (claim_id, str(date.today()), reason),
        )
        conn.commit()
        print(f"Appeal filed for claim {claim['claim_number']}; claim marked APPEALED.")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! {e}")
    finally:
        conn.close()


def resolve_appeal():
    print("\n-- Resolve Appeal --")
    conn = db.get_connection()
    try:
        appeal_id = prompt("Appeal ID: ", is_non_empty)
        appeal = conn.execute("SELECT * FROM appeal WHERE appeal_id=?", (appeal_id,)).fetchone()
        if not appeal:
            print("  ! No such appeal.")
            return
        status = prompt_choice("Resolution", ["RESOLVED", "REJECTED"])
        remarks = prompt("Resolution remarks: ", allow_blank=True)
        conn.execute(
            """UPDATE appeal SET appeal_status=?, resolution_date=?, resolution_remarks=?
               WHERE appeal_id=?""",
            (status, str(date.today()), remarks, appeal_id),
        )
        conn.commit()
        print("Appeal updated.")
    except db.DB_ERRORS as e:
        e = db.friendly_error(e)
        print(f"  ! {e}")
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 8. Search / lookups
# ----------------------------------------------------------------------
def search_menu():
    print("\n-- Search --")
    conn = db.get_connection()
    try:
        print("1. Search customer by name/phone/email")
        print("2. View policy details by policy number")
        print("3. View claim details by claim number")
        choice = input("Choice: ").strip()
        if choice == "1":
            term = input("Search term: ").strip()
            rows = conn.execute(
                """SELECT customer_id, first_name, last_name, phone, email, city FROM customer
                   WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR email LIKE ?""",
                tuple(f"%{term}%" for _ in range(4)),
            ).fetchall()
            print_rows(rows)
        elif choice == "2":
            pol_no = input("Policy number: ").strip()
            row = conn.execute(
                """SELECT p.policy_number, c.first_name||' '||c.last_name AS holder, pm.plan_name,
                          p.sum_insured, p.start_date, p.end_date, p.status
                   FROM policy p JOIN customer c ON p.customer_id=c.customer_id
                   JOIN plan_master pm ON p.plan_id=pm.plan_id WHERE p.policy_number=?""",
                (pol_no,),
            ).fetchall()
            print_rows(row)
        elif choice == "3":
            clm_no = input("Claim number: ").strip()
            row = conn.execute(
                """SELECT cl.claim_number, cl.status, cl.claim_date, cl.claimed_amount,
                          h.hospital_name, p.policy_number
                   FROM claim cl JOIN hospital h ON cl.hospital_id=h.hospital_id
                   JOIN policy p ON cl.policy_id=p.policy_id WHERE cl.claim_number=?""",
                (clm_no,),
            ).fetchall()
            print_rows(row)
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 9. Reports (backed by the views in sql/03_queries_and_views.sql)
# ----------------------------------------------------------------------
REPORTS = {
    "1": ("Active Policies", "SELECT * FROM vw_active_policies"),
    "2": ("Premium Dues", "SELECT * FROM vw_premium_dues"),
    "3": ("Pending Claims", "SELECT * FROM vw_pending_claims"),
    "4": ("Claim Approval Rate", "SELECT * FROM vw_claim_approval_rate"),
    "5": ("Settlement Report", "SELECT * FROM vw_settlement_report"),
    "6": ("Hospital-wise Claims", "SELECT * FROM vw_hospital_claims"),
    "7": ("Appeals Report", "SELECT * FROM vw_appeals_report"),
}


def reports_menu():
    print("\n-- Reports --")
    for key, (name, _) in REPORTS.items():
        print(f"{key}. {name}")
    choice = input("Choice: ").strip()
    if choice in REPORTS:
        name, query = REPORTS[choice]
        conn = db.get_connection()
        rows = conn.execute(query).fetchall()
        conn.close()
        print(f"\n=== {name} ===")
        print_rows(rows)
    else:
        print("  ! Invalid choice.")


# ----------------------------------------------------------------------
# Main menu
# ----------------------------------------------------------------------
MENU = """
=========== HIPCMS MAIN MENU ===========
 1. Add customer
 2. Add dependant
 3. Issue policy
 4. Collect premium
 5. Submit claim
 6. Verify claim / attach document
 7. Assess claim & record decision
 8. Settle claim
 9. File appeal
10. Resolve appeal
11. Search / lookup
12. Reports
 0. Logout & exit
=========================================
"""


def main():
    if "--reset" in sys.argv:
        db.build_fresh_database()
        print("Database reset to sample data.")

    ok, msg = db.test_connection()
    print(f"Database: {db.describe_connection()}")
    if not ok:
        print("\n  ! " + msg.replace("\n", "\n    "))
        return
    print(f"          {msg}")

    if not login():
        print("Too many failed attempts. Exiting.")
        return

    actions = {
        "1": add_customer,
        "2": add_dependant,
        "3": issue_policy,
        "4": collect_premium,
        "5": submit_claim,
        "6": verify_claim,
        "7": assess_claim,
        "8": settle_claim,
        "9": file_appeal,
        "10": resolve_appeal,
        "11": search_menu,
        "12": reports_menu,
    }

    while True:
        print(MENU)
        choice = input("Enter choice: ").strip()
        if choice == "0":
            print("Goodbye.")
            break
        action = actions.get(choice)
        if action:
            try:
                action()
            except Exception as e:
                print(f"  ! Unexpected error: {e}")
        else:
            print("  ! Invalid choice.")


if __name__ == "__main__":
    main()
