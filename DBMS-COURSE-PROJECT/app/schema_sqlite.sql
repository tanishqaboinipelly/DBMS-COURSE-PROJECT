-- =====================================================================
-- HIPCMS - SQLite port of the MySQL schema, used by the demo Python app.
-- Same entities, keys, and CHECK constraints as 01_schema_mysql.sql.
-- Business rules enforced by triggers (RAISE(ABORT, ...)) mirror the
-- MySQL SIGNAL-based triggers in the official DDL script.
-- =====================================================================
PRAGMA foreign_keys = ON;

CREATE TABLE users (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'AGENT' CHECK (role IN ('ADMIN','AGENT','ASSESSOR','CUSTOMER')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE customer (
    customer_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    dob             TEXT NOT NULL,
    gender          TEXT NOT NULL CHECK (gender IN ('M','F','O')),
    id_proof_number TEXT NOT NULL UNIQUE,
    phone           TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    address_line    TEXT NOT NULL,
    city            TEXT NOT NULL,
    state           TEXT NOT NULL,
    pincode         TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_customer_name ON customer (last_name, first_name);

CREATE TABLE dependant (
    dependant_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    dob             TEXT NOT NULL,
    gender          TEXT NOT NULL CHECK (gender IN ('M','F','O')),
    relationship    TEXT NOT NULL CHECK (relationship IN ('SPOUSE','SON','DAUGHTER','FATHER','MOTHER','OTHER'))
);
CREATE INDEX idx_dependant_customer ON dependant (customer_id);

CREATE TABLE plan_master (
    plan_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_name       TEXT NOT NULL UNIQUE,
    plan_type       TEXT NOT NULL CHECK (plan_type IN ('INDIVIDUAL','FAMILY_FLOATER','SENIOR_CITIZEN','GROUP')),
    coverage_amount REAL NOT NULL CHECK (coverage_amount > 0),
    premium_amount  REAL NOT NULL CHECK (premium_amount > 0),
    validity_months INTEGER NOT NULL DEFAULT 12,
    description     TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE policy (
    policy_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_number   TEXT NOT NULL UNIQUE,
    customer_id     INTEGER NOT NULL REFERENCES customer(customer_id),
    plan_id         INTEGER NOT NULL REFERENCES plan_master(plan_id),
    sum_insured     REAL NOT NULL CHECK (sum_insured > 0),
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL CHECK (end_date > start_date),
    status          TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','LAPSED','CANCELLED','EXPIRED')),
    issued_by       INTEGER REFERENCES users(user_id),
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_policy_customer ON policy (customer_id);
CREATE INDEX idx_policy_status ON policy (status);

CREATE TABLE premium (
    premium_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_id       INTEGER NOT NULL REFERENCES policy(policy_id) ON DELETE CASCADE,
    due_date        TEXT NOT NULL,
    amount_due      REAL NOT NULL CHECK (amount_due > 0),
    status          TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','PAID','OVERDUE')),
    UNIQUE (policy_id, due_date)
);
CREATE INDEX idx_premium_status ON premium (status);

CREATE TABLE payment (
    payment_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    premium_id      INTEGER NOT NULL REFERENCES premium(premium_id) ON DELETE CASCADE,
    payment_date    TEXT NOT NULL,
    amount_paid     REAL NOT NULL CHECK (amount_paid > 0),
    payment_mode    TEXT NOT NULL CHECK (payment_mode IN ('CASH','CARD','UPI','NETBANKING','CHEQUE')),
    transaction_ref TEXT NOT NULL UNIQUE
);

CREATE TABLE hospital (
    hospital_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name   TEXT NOT NULL,
    address_line    TEXT NOT NULL,
    city            TEXT NOT NULL,
    state           TEXT NOT NULL,
    network_type    TEXT NOT NULL CHECK (network_type IN ('NETWORK','NON_NETWORK')),
    contact_number  TEXT NOT NULL
);
CREATE INDEX idx_hospital_city ON hospital (city);

CREATE TABLE claim (
    claim_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_number    TEXT NOT NULL UNIQUE,
    policy_id       INTEGER NOT NULL REFERENCES policy(policy_id),
    dependant_id    INTEGER REFERENCES dependant(dependant_id),
    hospital_id     INTEGER NOT NULL REFERENCES hospital(hospital_id),
    claim_date      TEXT NOT NULL,
    claimed_amount  REAL NOT NULL CHECK (claimed_amount > 0),
    status          TEXT NOT NULL DEFAULT 'SUBMITTED'
        CHECK (status IN ('SUBMITTED','VERIFIED','UNDER_ASSESSMENT','APPROVED','REJECTED','SETTLED','APPEALED')),
    submitted_by    INTEGER REFERENCES users(user_id),
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_claim_policy ON claim (policy_id);
CREATE INDEX idx_claim_status ON claim (status);
CREATE INDEX idx_claim_date ON claim (claim_date);

CREATE TABLE treatment (
    treatment_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id        INTEGER NOT NULL REFERENCES claim(claim_id) ON DELETE CASCADE,
    treatment_name  TEXT NOT NULL,
    diagnosis       TEXT NOT NULL,
    admission_date  TEXT NOT NULL,
    discharge_date  TEXT NOT NULL CHECK (discharge_date >= admission_date),
    treatment_cost  REAL NOT NULL CHECK (treatment_cost > 0)
);
CREATE INDEX idx_treatment_claim ON treatment (claim_id);

CREATE TABLE claim_document (
    document_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id        INTEGER NOT NULL REFERENCES claim(claim_id) ON DELETE CASCADE,
    document_type   TEXT NOT NULL CHECK (document_type IN ('PRESCRIPTION','DISCHARGE_SUMMARY','BILL','LAB_REPORT','ID_PROOF','OTHER')),
    file_reference  TEXT NOT NULL,
    upload_date     TEXT NOT NULL
);
CREATE INDEX idx_document_claim ON claim_document (claim_id);

CREATE TABLE assessment (
    assessment_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id        INTEGER NOT NULL REFERENCES claim(claim_id) ON DELETE CASCADE,
    assessor_id     INTEGER NOT NULL REFERENCES users(user_id),
    assessment_date TEXT NOT NULL,
    assessed_amount REAL NOT NULL CHECK (assessed_amount >= 0),
    remarks         TEXT
);
CREATE INDEX idx_assessment_claim ON assessment (claim_id);

CREATE TABLE decision (
    decision_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id        INTEGER NOT NULL REFERENCES claim(claim_id) ON DELETE CASCADE,
    decision_date   TEXT NOT NULL,
    decision_status TEXT NOT NULL CHECK (decision_status IN ('APPROVED','REJECTED','PARTIALLY_APPROVED')),
    approved_amount REAL NOT NULL DEFAULT 0 CHECK (approved_amount >= 0),
    decided_by      INTEGER NOT NULL REFERENCES users(user_id)
);
CREATE INDEX idx_decision_claim ON decision (claim_id);

CREATE TABLE settlement (
    settlement_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id        INTEGER NOT NULL UNIQUE REFERENCES claim(claim_id) ON DELETE CASCADE,
    settlement_date TEXT NOT NULL,
    settled_amount  REAL NOT NULL CHECK (settled_amount > 0),
    settlement_mode TEXT NOT NULL CHECK (settlement_mode IN ('NEFT','CHEQUE','UPI')),
    transaction_ref TEXT NOT NULL UNIQUE
);

CREATE TABLE appeal (
    appeal_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id            INTEGER NOT NULL REFERENCES claim(claim_id) ON DELETE CASCADE,
    appeal_date         TEXT NOT NULL,
    reason              TEXT NOT NULL,
    appeal_status       TEXT NOT NULL DEFAULT 'PENDING' CHECK (appeal_status IN ('PENDING','RESOLVED','REJECTED')),
    resolution_date     TEXT,
    resolution_remarks  TEXT
);
CREATE INDEX idx_appeal_claim ON appeal (claim_id);

-- ---------------------------------------------------------------------
-- BUSINESS RULE TRIGGERS (mirrors 01_schema_mysql.sql)
-- ---------------------------------------------------------------------

-- Customer date of birth must be in the past
CREATE TRIGGER trg_customer_dob_past
BEFORE INSERT ON customer
FOR EACH ROW
WHEN NEW.dob >= date('now')
BEGIN
    SELECT RAISE(ABORT, 'Customer date of birth must be in the past');
END;

-- Active coverage required + treatment/claim date within validity
CREATE TRIGGER trg_claim_active_coverage
BEFORE INSERT ON claim
FOR EACH ROW
WHEN (SELECT status FROM policy WHERE policy_id = NEW.policy_id) <> 'ACTIVE'
BEGIN
    SELECT RAISE(ABORT, 'Claim rejected: policy is not ACTIVE');
END;

CREATE TRIGGER trg_claim_within_validity
BEFORE INSERT ON claim
FOR EACH ROW
WHEN NEW.claim_date < (SELECT start_date FROM policy WHERE policy_id = NEW.policy_id)
  OR NEW.claim_date > (SELECT end_date FROM policy WHERE policy_id = NEW.policy_id)
BEGIN
    SELECT RAISE(ABORT, 'Claim rejected: claim date outside policy validity period');
END;

-- No duplicate claims: same policy + hospital + date, not rejected
CREATE TRIGGER trg_claim_no_duplicate
BEFORE INSERT ON claim
FOR EACH ROW
WHEN (SELECT COUNT(*) FROM claim
      WHERE policy_id = NEW.policy_id
        AND hospital_id = NEW.hospital_id
        AND claim_date = NEW.claim_date
        AND status <> 'REJECTED') > 0
BEGIN
    SELECT RAISE(ABORT, 'Duplicate claim: identical claim already exists');
END;

-- Treatment dates within policy validity
CREATE TRIGGER trg_treatment_within_validity
BEFORE INSERT ON treatment
FOR EACH ROW
WHEN NEW.admission_date < (SELECT p.start_date FROM claim c JOIN policy p ON c.policy_id = p.policy_id WHERE c.claim_id = NEW.claim_id)
  OR NEW.discharge_date > (SELECT p.end_date FROM claim c JOIN policy p ON c.policy_id = p.policy_id WHERE c.claim_id = NEW.claim_id)
BEGIN
    SELECT RAISE(ABORT, 'Treatment dates fall outside the policy validity period');
END;

-- Settlement within limits (sum insured, and approved decision amount)
CREATE TRIGGER trg_settlement_within_limits
BEFORE INSERT ON settlement
FOR EACH ROW
WHEN NEW.settled_amount > (SELECT p.sum_insured FROM claim c JOIN policy p ON c.policy_id = p.policy_id WHERE c.claim_id = NEW.claim_id)
BEGIN
    SELECT RAISE(ABORT, 'Settlement exceeds policy sum insured');
END;

CREATE TRIGGER trg_settlement_within_approved
BEFORE INSERT ON settlement
FOR EACH ROW
WHEN (SELECT COALESCE(MAX(approved_amount),0) FROM decision WHERE claim_id = NEW.claim_id) > 0
 AND NEW.settled_amount > (SELECT MAX(approved_amount) FROM decision WHERE claim_id = NEW.claim_id)
BEGIN
    SELECT RAISE(ABORT, 'Settlement exceeds the approved decision amount');
END;

-- Status sync triggers
CREATE TRIGGER trg_after_decision_update_claim
AFTER INSERT ON decision
FOR EACH ROW
BEGIN
    UPDATE claim
    SET status = CASE NEW.decision_status
                    WHEN 'APPROVED' THEN 'APPROVED'
                    WHEN 'PARTIALLY_APPROVED' THEN 'APPROVED'
                    WHEN 'REJECTED' THEN 'REJECTED'
                 END
    WHERE claim_id = NEW.claim_id;
END;

CREATE TRIGGER trg_after_settlement_update_claim
AFTER INSERT ON settlement
FOR EACH ROW
BEGIN
    UPDATE claim SET status = 'SETTLED' WHERE claim_id = NEW.claim_id;
END;

CREATE TRIGGER trg_after_payment_update_premium
AFTER INSERT ON payment
FOR EACH ROW
BEGIN
    UPDATE premium SET status = 'PAID' WHERE premium_id = NEW.premium_id;
END;

CREATE TRIGGER trg_after_appeal_update_claim
AFTER INSERT ON appeal
FOR EACH ROW
BEGIN
    UPDATE claim SET status = 'APPEALED' WHERE claim_id = NEW.claim_id;
END;

-- ---------------------------------------------------------------------
-- REPORT VIEWS (mirrors 03_queries_and_views.sql)
-- ---------------------------------------------------------------------
CREATE VIEW vw_active_policies AS
SELECT p.policy_number,
       c.first_name || ' ' || c.last_name AS policyholder,
       pm.plan_name, p.sum_insured, p.start_date, p.end_date, p.status
FROM policy p
JOIN customer c ON p.customer_id = c.customer_id
JOIN plan_master pm ON p.plan_id = pm.plan_id
WHERE p.status = 'ACTIVE';

CREATE VIEW vw_premium_dues AS
SELECT pr.premium_id, p.policy_number,
       c.first_name || ' ' || c.last_name AS policyholder,
       pr.due_date, pr.amount_due, pr.status
FROM premium pr
JOIN policy p ON pr.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id
WHERE pr.status IN ('PENDING','OVERDUE');

CREATE VIEW vw_pending_claims AS
SELECT cl.claim_number, p.policy_number,
       c.first_name || ' ' || c.last_name AS policyholder,
       h.hospital_name, cl.claim_date, cl.claimed_amount, cl.status
FROM claim cl
JOIN policy p ON cl.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id
JOIN hospital h ON cl.hospital_id = h.hospital_id
WHERE cl.claim_id NOT IN (SELECT claim_id FROM decision);

CREATE VIEW vw_claim_approval_rate AS
SELECT
    COUNT(*) AS total_decided,
    COALESCE(SUM(CASE WHEN decision_status IN ('APPROVED','PARTIALLY_APPROVED') THEN 1 ELSE 0 END), 0) AS approved_count,
    COALESCE(SUM(CASE WHEN decision_status = 'REJECTED' THEN 1 ELSE 0 END), 0) AS rejected_count,
    COALESCE(ROUND(100.0 * SUM(CASE WHEN decision_status IN ('APPROVED','PARTIALLY_APPROVED') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2), 0.00) AS approval_rate_pct
FROM decision;

CREATE VIEW vw_settlement_report AS
SELECT s.transaction_ref, cl.claim_number, p.policy_number,
       c.first_name || ' ' || c.last_name AS policyholder,
       d.approved_amount, s.settled_amount, s.settlement_date, s.settlement_mode
FROM settlement s
JOIN claim cl ON s.claim_id = cl.claim_id
JOIN policy p ON cl.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id
JOIN decision d ON d.claim_id = cl.claim_id;

CREATE VIEW vw_hospital_claims AS
SELECT h.hospital_name, h.city,
       COUNT(cl.claim_id) AS total_claims,
       COALESCE(SUM(cl.claimed_amount),0) AS total_claimed_amount,
       ROUND(AVG(cl.claimed_amount),2) AS avg_claim_amount
FROM hospital h
LEFT JOIN claim cl ON h.hospital_id = cl.hospital_id
GROUP BY h.hospital_id, h.hospital_name, h.city
ORDER BY total_claims DESC;

CREATE VIEW vw_appeals_report AS
SELECT a.appeal_id, cl.claim_number,
       c.first_name || ' ' || c.last_name AS policyholder,
       a.appeal_date, a.reason, a.appeal_status, a.resolution_date
FROM appeal a
JOIN claim cl ON a.claim_id = cl.claim_id
JOIN policy p ON cl.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id;
