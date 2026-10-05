-- =====================================================================
-- QUERIES & VIEWS - HIPCMS
-- Demonstrates: joins, aggregate functions, nested/sub-queries, views
-- =====================================================================
USE hipcms;

-- ---------------------------------------------------------------------
-- 1. ACTIVE POLICIES REPORT (join)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_active_policies AS
SELECT p.policy_number,
       CONCAT(c.first_name,' ',c.last_name) AS policyholder,
       pm.plan_name,
       p.sum_insured,
       p.start_date,
       p.end_date,
       p.status
FROM policy p
JOIN customer c    ON p.customer_id = c.customer_id
JOIN plan_master pm ON p.plan_id = pm.plan_id
WHERE p.status = 'ACTIVE';

SELECT * FROM vw_active_policies;

-- ---------------------------------------------------------------------
-- 2. PREMIUM DUES REPORT (join + filter)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_premium_dues AS
SELECT pr.premium_id,
       p.policy_number,
       CONCAT(c.first_name,' ',c.last_name) AS policyholder,
       pr.due_date,
       pr.amount_due,
       pr.status
FROM premium pr
JOIN policy p   ON pr.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id
WHERE pr.status IN ('PENDING','OVERDUE');

SELECT * FROM vw_premium_dues;

-- ---------------------------------------------------------------------
-- 3. PENDING CLAIMS REPORT (nested subquery: claims with no decision yet)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_pending_claims AS
SELECT cl.claim_number,
       p.policy_number,
       CONCAT(c.first_name,' ',c.last_name) AS policyholder,
       h.hospital_name,
       cl.claim_date,
       cl.claimed_amount,
       cl.status
FROM claim cl
JOIN policy p   ON cl.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id
JOIN hospital h ON cl.hospital_id = h.hospital_id
WHERE cl.claim_id NOT IN (SELECT claim_id FROM decision);

SELECT * FROM vw_pending_claims;

-- ---------------------------------------------------------------------
-- 4. CLAIM APPROVAL RATE REPORT (aggregate functions)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_claim_approval_rate AS
SELECT
    COUNT(*)                                                        AS total_decided,
    COALESCE(SUM(CASE WHEN decision_status IN ('APPROVED','PARTIALLY_APPROVED')
             THEN 1 ELSE 0 END), 0)                                  AS approved_count,
    COALESCE(SUM(CASE WHEN decision_status = 'REJECTED' THEN 1 ELSE 0 END), 0) AS rejected_count,
    COALESCE(ROUND( 100 * SUM(CASE WHEN decision_status IN ('APPROVED','PARTIALLY_APPROVED')
                          THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2), 0.00)  AS approval_rate_pct
FROM decision;

SELECT * FROM vw_claim_approval_rate;

-- ---------------------------------------------------------------------
-- 5. SETTLEMENT REPORT (join across claim -> decision -> settlement)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_settlement_report AS
SELECT s.transaction_ref,
       cl.claim_number,
       p.policy_number,
       CONCAT(c.first_name,' ',c.last_name) AS policyholder,
       d.approved_amount,
       s.settled_amount,
       s.settlement_date,
       s.settlement_mode
FROM settlement s
JOIN claim cl    ON s.claim_id = cl.claim_id
JOIN policy p    ON cl.policy_id = p.policy_id
JOIN customer c  ON p.customer_id = c.customer_id
JOIN decision d  ON d.claim_id = cl.claim_id;

SELECT * FROM vw_settlement_report;

-- ---------------------------------------------------------------------
-- 6. HOSPITAL-WISE CLAIMS REPORT (aggregate + group by)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_hospital_claims AS
SELECT h.hospital_name,
       h.city,
       COUNT(cl.claim_id)               AS total_claims,
       SUM(cl.claimed_amount)           AS total_claimed_amount,
       ROUND(AVG(cl.claimed_amount),2)  AS avg_claim_amount
FROM hospital h
LEFT JOIN claim cl ON h.hospital_id = cl.hospital_id
GROUP BY h.hospital_id, h.hospital_name, h.city
ORDER BY total_claims DESC;

SELECT * FROM vw_hospital_claims;

-- ---------------------------------------------------------------------
-- 7. APPEALS REPORT
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_appeals_report AS
SELECT a.appeal_id,
       cl.claim_number,
       CONCAT(c.first_name,' ',c.last_name) AS policyholder,
       a.appeal_date,
       a.reason,
       a.appeal_status,
       a.resolution_date
FROM appeal a
JOIN claim cl   ON a.claim_id = cl.claim_id
JOIN policy p   ON cl.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id;

SELECT * FROM vw_appeals_report;

-- ---------------------------------------------------------------------
-- 8. CUSTOMERS WHOSE CLAIMED AMOUNT EXCEEDS THE AVERAGE CLAIM
--    (correlated aggregate + subquery)
-- ---------------------------------------------------------------------
SELECT CONCAT(c.first_name,' ',c.last_name) AS policyholder,
       cl.claim_number,
       cl.claimed_amount
FROM claim cl
JOIN policy p   ON cl.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id
WHERE cl.claimed_amount > (SELECT AVG(claimed_amount) FROM claim);

-- ---------------------------------------------------------------------
-- 9. POLICIES WITH NO CLAIMS AT ALL (NOT EXISTS subquery)
-- ---------------------------------------------------------------------
SELECT p.policy_number, CONCAT(c.first_name,' ',c.last_name) AS policyholder
FROM policy p
JOIN customer c ON p.customer_id = c.customer_id
WHERE NOT EXISTS (SELECT 1 FROM claim cl WHERE cl.policy_id = p.policy_id);

-- ---------------------------------------------------------------------
-- 10. TOTAL PREMIUM COLLECTED PER PLAN (aggregate + join + group by)
-- ---------------------------------------------------------------------
SELECT pm.plan_name,
       COUNT(DISTINCT po.policy_id) AS policy_count,
       SUM(pay.amount_paid)        AS total_collected
FROM plan_master pm
JOIN policy po   ON pm.plan_id = po.plan_id
JOIN premium pr  ON po.policy_id = pr.policy_id
JOIN payment pay ON pr.premium_id = pay.premium_id
GROUP BY pm.plan_id, pm.plan_name
ORDER BY total_collected DESC;

-- ---------------------------------------------------------------------
-- 11. CLAIMS APPROACHING/AT RISK OF DUPLICATE (same policy/hospital/date)
--     -- demonstrates HAVING with GROUP BY
-- ---------------------------------------------------------------------
SELECT policy_id, hospital_id, claim_date, COUNT(*) AS occurrences
FROM claim
GROUP BY policy_id, hospital_id, claim_date
HAVING COUNT(*) > 1;

-- ---------------------------------------------------------------------
-- 12. TOP 3 CUSTOMERS BY TOTAL SETTLED AMOUNT (nested aggregation + LIMIT)
-- ---------------------------------------------------------------------
SELECT CONCAT(c.first_name,' ',c.last_name) AS policyholder,
       SUM(s.settled_amount) AS total_settled
FROM settlement s
JOIN claim cl   ON s.claim_id = cl.claim_id
JOIN policy p   ON cl.policy_id = p.policy_id
JOIN customer c ON p.customer_id = c.customer_id
GROUP BY c.customer_id
ORDER BY total_settled DESC
LIMIT 3;
