-- =====================================================================
-- HEALTH INSURANCE POLICY AND CLAIMS MANAGEMENT SYSTEM (HIPCMS)
-- DDL Script - MySQL 8.0+
-- Normalized to Third Normal Form (3NF)
-- =====================================================================

DROP DATABASE IF EXISTS hipcms;
CREATE DATABASE hipcms CHARACTER SET utf8mb4;
USE hipcms;

-- =====================================================================
-- 1. USERS (application login / role-based access)
-- =====================================================================
CREATE TABLE users (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'AGENT',
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_user_role CHECK (role IN ('ADMIN','AGENT','ASSESSOR','CUSTOMER'))
);

-- =====================================================================
-- 2. CUSTOMER
-- =====================================================================
CREATE TABLE customer (
    customer_id     INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    dob             DATE NOT NULL,
    gender          CHAR(1) NOT NULL,
    id_proof_number VARCHAR(20) NOT NULL UNIQUE,   -- e.g. Aadhar / national ID
    phone           VARCHAR(15) NOT NULL,
    email           VARCHAR(100) NOT NULL UNIQUE,
    address_line    VARCHAR(150) NOT NULL,
    city            VARCHAR(50) NOT NULL,
    state           VARCHAR(50) NOT NULL,
    pincode         VARCHAR(10) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_customer_gender CHECK (gender IN ('M','F','O'))
);

CREATE INDEX idx_customer_name ON customer (last_name, first_name);
CREATE INDEX idx_customer_phone ON customer (phone);

-- =====================================================================
-- 3. DEPENDANT
-- =====================================================================
CREATE TABLE dependant (
    dependant_id    INT AUTO_INCREMENT PRIMARY KEY,
    customer_id     INT NOT NULL,
    first_name      VARCHAR(50) NOT NULL,
    last_name       VARCHAR(50) NOT NULL,
    dob             DATE NOT NULL,
    gender          CHAR(1) NOT NULL,
    relationship    VARCHAR(20) NOT NULL,
    CONSTRAINT fk_dependant_customer FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id) ON DELETE CASCADE,
    CONSTRAINT chk_dependant_gender CHECK (gender IN ('M','F','O')),
    CONSTRAINT chk_dependant_relationship CHECK (
        relationship IN ('SPOUSE','SON','DAUGHTER','FATHER','MOTHER','OTHER')
    )
);

CREATE INDEX idx_dependant_customer ON dependant (customer_id);

-- =====================================================================
-- 4. PLAN (insurance product master)
-- =====================================================================
CREATE TABLE plan_master (
    plan_id         INT AUTO_INCREMENT PRIMARY KEY,
    plan_name       VARCHAR(100) NOT NULL UNIQUE,
    plan_type       VARCHAR(20) NOT NULL,
    coverage_amount DECIMAL(12,2) NOT NULL,
    premium_amount  DECIMAL(10,2) NOT NULL,
    validity_months INT NOT NULL DEFAULT 12,
    description     VARCHAR(255),
    is_active       TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT chk_plan_type CHECK (plan_type IN ('INDIVIDUAL','FAMILY_FLOATER','SENIOR_CITIZEN','GROUP')),
    CONSTRAINT chk_plan_coverage CHECK (coverage_amount > 0),
    CONSTRAINT chk_plan_premium CHECK (premium_amount > 0)
);

-- =====================================================================
-- 5. POLICY
-- =====================================================================
CREATE TABLE policy (
    policy_id       INT AUTO_INCREMENT PRIMARY KEY,
    policy_number   VARCHAR(20) NOT NULL UNIQUE,
    customer_id     INT NOT NULL,
    plan_id         INT NOT NULL,
    sum_insured     DECIMAL(12,2) NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    status          VARCHAR(15) NOT NULL DEFAULT 'ACTIVE',
    issued_by       INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_policy_customer FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id) ON DELETE RESTRICT,
    CONSTRAINT fk_policy_plan FOREIGN KEY (plan_id)
        REFERENCES plan_master(plan_id) ON DELETE RESTRICT,
    CONSTRAINT fk_policy_issuer FOREIGN KEY (issued_by)
        REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT chk_policy_status CHECK (status IN ('ACTIVE','LAPSED','CANCELLED','EXPIRED')),
    CONSTRAINT chk_policy_dates CHECK (end_date > start_date),
    CONSTRAINT chk_policy_sum_insured CHECK (sum_insured > 0)
);

CREATE INDEX idx_policy_customer ON policy (customer_id);
CREATE INDEX idx_policy_status ON policy (status);

-- =====================================================================
-- 6. PREMIUM (installment schedule for a policy)
-- =====================================================================
CREATE TABLE premium (
    premium_id      INT AUTO_INCREMENT PRIMARY KEY,
    policy_id       INT NOT NULL,
    due_date        DATE NOT NULL,
    amount_due      DECIMAL(10,2) NOT NULL,
    status          VARCHAR(15) NOT NULL DEFAULT 'PENDING',
    CONSTRAINT fk_premium_policy FOREIGN KEY (policy_id)
        REFERENCES policy(policy_id) ON DELETE CASCADE,
    CONSTRAINT chk_premium_status CHECK (status IN ('PENDING','PAID','OVERDUE')),
    CONSTRAINT chk_premium_amount CHECK (amount_due > 0),
    CONSTRAINT uq_premium_policy_due UNIQUE (policy_id, due_date)
);

CREATE INDEX idx_premium_status ON premium (status);

-- =====================================================================
-- 7. PAYMENT (actual receipt against a premium installment)
-- =====================================================================
CREATE TABLE payment (
    payment_id      INT AUTO_INCREMENT PRIMARY KEY,
    premium_id      INT NOT NULL,
    payment_date    DATE NOT NULL,
    amount_paid     DECIMAL(10,2) NOT NULL,
    payment_mode    VARCHAR(15) NOT NULL,
    transaction_ref VARCHAR(30) NOT NULL UNIQUE,
    CONSTRAINT fk_payment_premium FOREIGN KEY (premium_id)
        REFERENCES premium(premium_id) ON DELETE CASCADE,
    CONSTRAINT chk_payment_mode CHECK (payment_mode IN ('CASH','CARD','UPI','NETBANKING','CHEQUE')),
    CONSTRAINT chk_payment_amount CHECK (amount_paid > 0)
);

-- =====================================================================
-- 8. HOSPITAL
-- =====================================================================
CREATE TABLE hospital (
    hospital_id     INT AUTO_INCREMENT PRIMARY KEY,
    hospital_name   VARCHAR(100) NOT NULL,
    address_line    VARCHAR(150) NOT NULL,
    city            VARCHAR(50) NOT NULL,
    state           VARCHAR(50) NOT NULL,
    network_type    VARCHAR(15) NOT NULL,
    contact_number  VARCHAR(15) NOT NULL,
    CONSTRAINT chk_hospital_network CHECK (network_type IN ('NETWORK','NON_NETWORK'))
);

CREATE INDEX idx_hospital_city ON hospital (city);

-- =====================================================================
-- 9. CLAIM
-- =====================================================================
CREATE TABLE claim (
    claim_id        INT AUTO_INCREMENT PRIMARY KEY,
    claim_number    VARCHAR(20) NOT NULL UNIQUE,
    policy_id       INT NOT NULL,
    dependant_id    INT NULL,               -- NULL => claim is for the policyholder
    hospital_id     INT NOT NULL,
    claim_date      DATE NOT NULL,
    claimed_amount  DECIMAL(12,2) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'SUBMITTED',
    submitted_by    INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_claim_policy FOREIGN KEY (policy_id)
        REFERENCES policy(policy_id) ON DELETE RESTRICT,
    CONSTRAINT fk_claim_dependant FOREIGN KEY (dependant_id)
        REFERENCES dependant(dependant_id) ON DELETE SET NULL,
    CONSTRAINT fk_claim_hospital FOREIGN KEY (hospital_id)
        REFERENCES hospital(hospital_id) ON DELETE RESTRICT,
    CONSTRAINT fk_claim_user FOREIGN KEY (submitted_by)
        REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT chk_claim_status CHECK (
        status IN ('SUBMITTED','VERIFIED','UNDER_ASSESSMENT','APPROVED','REJECTED','SETTLED','APPEALED')
    ),
    CONSTRAINT chk_claim_amount CHECK (claimed_amount > 0)
);

CREATE INDEX idx_claim_policy ON claim (policy_id);
CREATE INDEX idx_claim_status ON claim (status);
CREATE INDEX idx_claim_date ON claim (claim_date);

-- =====================================================================
-- 10. TREATMENT (one row per treatment/admission line under a claim)
-- =====================================================================
CREATE TABLE treatment (
    treatment_id    INT AUTO_INCREMENT PRIMARY KEY,
    claim_id        INT NOT NULL,
    treatment_name  VARCHAR(100) NOT NULL,
    diagnosis       VARCHAR(150) NOT NULL,
    admission_date  DATE NOT NULL,
    discharge_date  DATE NOT NULL,
    treatment_cost  DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_treatment_claim FOREIGN KEY (claim_id)
        REFERENCES claim(claim_id) ON DELETE CASCADE,
    CONSTRAINT chk_treatment_dates CHECK (discharge_date >= admission_date),
    CONSTRAINT chk_treatment_cost CHECK (treatment_cost > 0)
);

CREATE INDEX idx_treatment_claim ON treatment (claim_id);

-- =====================================================================
-- 11. CLAIM_DOCUMENT
-- =====================================================================
CREATE TABLE claim_document (
    document_id     INT AUTO_INCREMENT PRIMARY KEY,
    claim_id        INT NOT NULL,
    document_type   VARCHAR(30) NOT NULL,
    file_reference  VARCHAR(255) NOT NULL,
    upload_date     DATE NOT NULL,
    CONSTRAINT fk_document_claim FOREIGN KEY (claim_id)
        REFERENCES claim(claim_id) ON DELETE CASCADE,
    CONSTRAINT chk_document_type CHECK (
        document_type IN ('PRESCRIPTION','DISCHARGE_SUMMARY','BILL','LAB_REPORT','ID_PROOF','OTHER')
    )
);

CREATE INDEX idx_document_claim ON claim_document (claim_id);

-- =====================================================================
-- 12. ASSESSMENT
-- =====================================================================
CREATE TABLE assessment (
    assessment_id   INT AUTO_INCREMENT PRIMARY KEY,
    claim_id        INT NOT NULL,
    assessor_id     INT NOT NULL,
    assessment_date DATE NOT NULL,
    assessed_amount DECIMAL(12,2) NOT NULL,
    remarks         VARCHAR(255),
    CONSTRAINT fk_assessment_claim FOREIGN KEY (claim_id)
        REFERENCES claim(claim_id) ON DELETE CASCADE,
    CONSTRAINT fk_assessment_assessor FOREIGN KEY (assessor_id)
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT chk_assessment_amount CHECK (assessed_amount >= 0)
);

CREATE INDEX idx_assessment_claim ON assessment (claim_id);

-- =====================================================================
-- 13. DECISION
-- =====================================================================
CREATE TABLE decision (
    decision_id     INT AUTO_INCREMENT PRIMARY KEY,
    claim_id        INT NOT NULL,
    decision_date   DATE NOT NULL,
    decision_status VARCHAR(20) NOT NULL,
    approved_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    decided_by      INT NOT NULL,
    CONSTRAINT fk_decision_claim FOREIGN KEY (claim_id)
        REFERENCES claim(claim_id) ON DELETE CASCADE,
    CONSTRAINT fk_decision_user FOREIGN KEY (decided_by)
        REFERENCES users(user_id) ON DELETE RESTRICT,
    CONSTRAINT chk_decision_status CHECK (
        decision_status IN ('APPROVED','REJECTED','PARTIALLY_APPROVED')
    ),
    CONSTRAINT chk_decision_amount CHECK (approved_amount >= 0)
);

CREATE INDEX idx_decision_claim ON decision (claim_id);

-- =====================================================================
-- 14. SETTLEMENT
-- =====================================================================
CREATE TABLE settlement (
    settlement_id   INT AUTO_INCREMENT PRIMARY KEY,
    claim_id        INT NOT NULL UNIQUE,     -- one settlement per claim
    settlement_date DATE NOT NULL,
    settled_amount  DECIMAL(12,2) NOT NULL,
    settlement_mode VARCHAR(15) NOT NULL,
    transaction_ref VARCHAR(30) NOT NULL UNIQUE,
    CONSTRAINT fk_settlement_claim FOREIGN KEY (claim_id)
        REFERENCES claim(claim_id) ON DELETE CASCADE,
    CONSTRAINT chk_settlement_mode CHECK (settlement_mode IN ('NEFT','CHEQUE','UPI')),
    CONSTRAINT chk_settlement_amount CHECK (settled_amount > 0)
);

-- =====================================================================
-- 15. APPEAL
-- =====================================================================
CREATE TABLE appeal (
    appeal_id           INT AUTO_INCREMENT PRIMARY KEY,
    claim_id            INT NOT NULL,
    appeal_date         DATE NOT NULL,
    reason              VARCHAR(255) NOT NULL,
    appeal_status       VARCHAR(15) NOT NULL DEFAULT 'PENDING',
    resolution_date     DATE,
    resolution_remarks  VARCHAR(255),
    CONSTRAINT fk_appeal_claim FOREIGN KEY (claim_id)
        REFERENCES claim(claim_id) ON DELETE CASCADE,
    CONSTRAINT chk_appeal_status CHECK (appeal_status IN ('PENDING','RESOLVED','REJECTED'))
);

CREATE INDEX idx_appeal_claim ON appeal (claim_id);

-- =====================================================================
-- BUSINESS-RULE TRIGGERS
-- (cross-table rules that a single-row CHECK constraint cannot express)
-- =====================================================================
DELIMITER $$

-- Rule: a customer's date of birth must be in the past. CURDATE() cannot be
-- used inside a CHECK constraint (MySQL disallows non-deterministic
-- functions there), so this is enforced with a trigger instead.
CREATE TRIGGER trg_customer_dob_past
BEFORE INSERT ON customer
FOR EACH ROW
BEGIN
    IF NEW.dob >= CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Customer date of birth must be in the past';
    END IF;
END$$

-- Rule: a claim can only be submitted against a policy that is ACTIVE
-- and whose validity period covers the claim date.
CREATE TRIGGER trg_claim_active_coverage
BEFORE INSERT ON claim
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(15);
    DECLARE v_start DATE;
    DECLARE v_end DATE;

    SELECT status, start_date, end_date INTO v_status, v_start, v_end
    FROM policy WHERE policy_id = NEW.policy_id;

    IF v_status <> 'ACTIVE' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Claim rejected: policy is not ACTIVE';
    END IF;

    IF NEW.claim_date < v_start OR NEW.claim_date > v_end THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Claim rejected: claim date is outside policy validity period';
    END IF;
END$$

-- Rule: no duplicate claims -- same policy, same hospital, same claim date
-- already exists in a non-rejected state.
CREATE TRIGGER trg_claim_no_duplicate
BEFORE INSERT ON claim
FOR EACH ROW
BEGIN
    DECLARE v_count INT;

    SELECT COUNT(*) INTO v_count
    FROM claim
    WHERE policy_id = NEW.policy_id
      AND hospital_id = NEW.hospital_id
      AND claim_date = NEW.claim_date
      AND status <> 'REJECTED';

    IF v_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Duplicate claim: an identical claim already exists for this policy/hospital/date';
    END IF;
END$$

-- Rule: treatment admission/discharge dates must fall within the policy
-- validity period of the associated claim's policy.
CREATE TRIGGER trg_treatment_within_validity
BEFORE INSERT ON treatment
FOR EACH ROW
BEGIN
    DECLARE v_start DATE;
    DECLARE v_end DATE;

    SELECT p.start_date, p.end_date INTO v_start, v_end
    FROM claim c JOIN policy p ON c.policy_id = p.policy_id
    WHERE c.claim_id = NEW.claim_id;

    IF NEW.admission_date < v_start OR NEW.discharge_date > v_end THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Treatment dates fall outside the policy validity period';
    END IF;
END$$

-- Rule: settlement amount must never exceed the policy's sum insured,
-- and must not exceed the approved amount on the claim's decision.
CREATE TRIGGER trg_settlement_within_limits
BEFORE INSERT ON settlement
FOR EACH ROW
BEGIN
    DECLARE v_sum_insured DECIMAL(12,2);
    DECLARE v_approved DECIMAL(12,2);

    SELECT p.sum_insured INTO v_sum_insured
    FROM claim c JOIN policy p ON c.policy_id = p.policy_id
    WHERE c.claim_id = NEW.claim_id;

    SELECT COALESCE(MAX(approved_amount),0) INTO v_approved
    FROM decision WHERE claim_id = NEW.claim_id;

    IF NEW.settled_amount > v_sum_insured THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Settlement exceeds policy sum insured';
    END IF;

    IF v_approved > 0 AND NEW.settled_amount > v_approved THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Settlement exceeds the approved decision amount';
    END IF;
END$$

-- Keep claim.status and premium.status in sync with downstream events.
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
END$$

CREATE TRIGGER trg_after_settlement_update_claim
AFTER INSERT ON settlement
FOR EACH ROW
BEGIN
    UPDATE claim SET status = 'SETTLED' WHERE claim_id = NEW.claim_id;
END$$

CREATE TRIGGER trg_after_payment_update_premium
AFTER INSERT ON payment
FOR EACH ROW
BEGIN
    UPDATE premium SET status = 'PAID' WHERE premium_id = NEW.premium_id;
END$$

CREATE TRIGGER trg_after_appeal_update_claim
AFTER INSERT ON appeal
FOR EACH ROW
BEGIN
    UPDATE claim SET status = 'APPEALED' WHERE claim_id = NEW.claim_id;
END$$

DELIMITER ;
