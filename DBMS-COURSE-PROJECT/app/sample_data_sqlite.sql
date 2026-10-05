INSERT INTO users (username, password_hash, full_name, role) VALUES
('admin','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','System Administrator','ADMIN'),
('agent1','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','Ramesh Kumar','AGENT'),
('agent2','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','Sunita Rao','AGENT'),
('assessor1','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','Dr. Vinod Nair','ASSESSOR'),
('assessor2','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','Dr. Priya Menon','ASSESSOR');

-- CUSTOMERS (15)
INSERT INTO customer (first_name,last_name,dob,gender,id_proof_number,phone,email,address_line,city,state,pincode) VALUES
('Arun','Sharma','1985-04-12','M','ID100001','9876500001','arun.sharma@example.com','12 MG Road','Chennai','Tamil Nadu','600001'),
('Divya','Iyer','1990-08-25','F','ID100002','9876500002','divya.iyer@example.com','45 Anna Nagar','Chennai','Tamil Nadu','600040'),
('Karthik','Reddy','1978-01-30','M','ID100003','9876500003','karthik.reddy@example.com','7 Jubilee Hills','Hyderabad','Telangana','500033'),
('Sneha','Patil','1995-11-05','F','ID100004','9876500004','sneha.patil@example.com','23 FC Road','Pune','Maharashtra','411005'),
('Mohammed','Ali','1982-06-18','M','ID100005','9876500005','mohammed.ali@example.com','9 Banjara Hills','Hyderabad','Telangana','500034'),
('Lakshmi','Narayanan','1970-03-22','F','ID100006','9876500006','lakshmi.n@example.com','56 T Nagar','Chennai','Tamil Nadu','600017'),
('Rajesh','Kumar','1988-09-14','M','ID100007','9876500007','rajesh.kumar@example.com','18 Indiranagar','Bengaluru','Karnataka','560038'),
('Priya','Venkatesh','1992-12-02','F','ID100008','9876500008','priya.venkatesh@example.com','27 Koramangala','Bengaluru','Karnataka','560034'),
('Anil','Kapoor','1975-07-19','M','ID100009','9876500009','anil.kapoor@example.com','5 Andheri West','Mumbai','Maharashtra','400058'),
('Sunita','Rao','1983-02-27','F','ID100010','9876500010','sunita.rao@example.com','61 Bandra','Mumbai','Maharashtra','400050'),
('Vikram','Singh','1980-10-09','M','ID100011','9876500011','vikram.singh@example.com','33 Connaught Place','New Delhi','Delhi','110001'),
('Neha','Gupta','1993-05-16','F','ID100012','9876500012','neha.gupta@example.com','8 Karol Bagh','New Delhi','Delhi','110005'),
('Suresh','Babu','1972-01-08','M','ID100013','9876500013','suresh.babu@example.com','14 RS Puram','Coimbatore','Tamil Nadu','641002'),
('Kavya','Krishnan','1991-03-29','F','ID100014','9876500014','kavya.krishnan@example.com','21 MG Road','Kochi','Kerala','682016'),
('Ramesh','Iyer','1968-11-11','M','ID100015','9876500015','ramesh.iyer@example.com','3 Anna Nagar','Madurai','Tamil Nadu','625020');

-- DEPENDANTS (12)
INSERT INTO dependant (customer_id, first_name, last_name, dob, gender, relationship) VALUES
(1,'Meena','Sharma','1988-02-14','F','SPOUSE'),
(1,'Rohan','Sharma','2015-07-09','M','SON'),
(2,'Suresh','Iyer','1987-05-19','M','SPOUSE'),
(3,'Anitha','Reddy','1980-09-02','F','SPOUSE'),
(5,'Zara','Ali','2018-12-01','F','DAUGHTER'),
(7,'Kavitha','Kumar','1990-04-11','F','SPOUSE'),
(7,'Arjun','Kumar','2016-08-23','M','SON'),
(9,'Pooja','Kapoor','1979-06-30','F','SPOUSE'),
(11,'Meera','Singh','1984-01-17','F','SPOUSE'),
(13,'Divya','Babu','1975-03-05','F','SPOUSE'),
(14,'Rahul','Krishnan','2017-09-12','M','SON'),
(15,'Anjali','Iyer','2019-02-27','F','DAUGHTER');

-- PLANS (5)
INSERT INTO plan_master (plan_name, plan_type, coverage_amount, premium_amount, validity_months, description) VALUES
('HealthSecure Individual Basic','INDIVIDUAL',300000.00,8500.00,12,'Basic individual hospitalization cover'),
('HealthSecure Family Floater Gold','FAMILY_FLOATER',1000000.00,22000.00,12,'Family floater covering self, spouse and children'),
('SeniorCare Plus','SENIOR_CITIZEN',500000.00,18000.00,12,'Tailored plan for citizens above 60'),
('CorpShield Group Cover','GROUP',2000000.00,15000.00,12,'Group policy for corporate employees'),
('SmartCare Micro','INDIVIDUAL',150000.00,4500.00,12,'Low-premium micro cover for young individuals');

-- HOSPITALS (8)
INSERT INTO hospital (hospital_name, address_line, city, state, network_type, contact_number) VALUES
('Apollo Speciality Hospital','21 Greams Road','Chennai','Tamil Nadu','NETWORK','04428290000'),
('Care Hospitals','Road No.1 Banjara Hills','Hyderabad','Telangana','NETWORK','04030417000'),
('Ruby Hall Clinic','40 Sassoon Road','Pune','Maharashtra','NETWORK','02066455100'),
('City General Hospital','8 Poonamallee High Road','Chennai','Tamil Nadu','NON_NETWORK','04423456789'),
('Manipal Hospital','98 HAL Airport Road','Bengaluru','Karnataka','NETWORK','08025024444'),
('Lilavati Hospital','A791 Bandra Reclamation','Mumbai','Maharashtra','NETWORK','02226751000'),
('Fortis Escorts Heart Institute','Okhla Road','New Delhi','Delhi','NETWORK','01147135000'),
('KIMS Hospital','Panampilly Nagar','Kochi','Kerala','NON_NETWORK','04842801000');

-- POLICIES (15) -- policy_id follows insertion order 1..15
INSERT INTO policy (policy_number, customer_id, plan_id, sum_insured, start_date, end_date, status, issued_by) VALUES
('POL-2025-0001',1,2,1000000.00,'2025-01-01','2025-12-31','ACTIVE',2),
('POL-2025-0002',2,1,300000.00,'2025-02-15','2026-02-14','ACTIVE',2),
('POL-2025-0003',3,2,1000000.00,'2024-06-01','2025-05-31','EXPIRED',3),
('POL-2025-0004',4,1,300000.00,'2025-03-01','2026-02-28','ACTIVE',3),
('POL-2025-0005',5,2,1000000.00,'2025-01-10','2025-12-31','ACTIVE',2),
('POL-2025-0006',6,3,500000.00,'2025-04-01','2026-03-31','ACTIVE',3),
('POL-2025-0007',7,2,1000000.00,'2025-05-01','2026-04-30','ACTIVE',2),
('POL-2025-0008',8,1,300000.00,'2025-02-01','2026-01-31','ACTIVE',2),
('POL-2025-0009',9,4,2000000.00,'2025-01-15','2025-12-31','ACTIVE',3),
('POL-2025-0010',10,5,150000.00,'2025-06-01','2026-05-31','ACTIVE',2),
('POL-2025-0011',11,2,1000000.00,'2024-01-01','2024-12-31','EXPIRED',3),
('POL-2025-0012',12,1,300000.00,'2025-07-01','2026-06-30','ACTIVE',2),
('POL-2025-0013',13,3,500000.00,'2025-03-15','2026-03-14','ACTIVE',3),
('POL-2025-0014',14,5,150000.00,'2025-08-01','2026-07-31','ACTIVE',2),
('POL-2025-0015',15,2,1000000.00,'2025-01-01','2025-06-30','LAPSED',3);

-- PREMIUMS (20: one initial installment per policy + 5 renewal installments)
INSERT INTO premium (policy_id, due_date, amount_due, status) VALUES
(1,'2025-01-01',22000.00,'PENDING'),
(2,'2025-02-15',8500.00,'PENDING'),
(3,'2024-06-01',22000.00,'PENDING'),
(4,'2025-03-01',8500.00,'PENDING'),
(5,'2025-01-10',22000.00,'PENDING'),
(6,'2025-04-01',18000.00,'PENDING'),
(7,'2025-05-01',22000.00,'PENDING'),
(8,'2025-02-01',8500.00,'PENDING'),
(9,'2025-01-15',15000.00,'PENDING'),
(10,'2025-06-01',4500.00,'PENDING'),
(11,'2024-01-01',22000.00,'PENDING'),
(12,'2025-07-01',8500.00,'PENDING'),
(13,'2025-03-15',18000.00,'PENDING'),
(14,'2025-08-01',4500.00,'PENDING'),
(15,'2025-01-01',22000.00,'PENDING'),
(1,'2026-01-01',22000.00,'PENDING'),
(4,'2026-03-01',8500.00,'PENDING'),
(5,'2026-01-10',22000.00,'PENDING'),
(9,'2026-01-15',15000.00,'PENDING'),
(13,'2026-03-15',18000.00,'PENDING');

-- PAYMENTS (12 initial installments paid; policies 8, 12 and 14's initial dues
-- and all 5 renewal installments are deliberately left PENDING/OVERDUE so the
-- "premium dues" report has non-trivial results)
INSERT INTO payment (premium_id, payment_date, amount_paid, payment_mode, transaction_ref) VALUES
(1,'2025-01-02',22000.00,'UPI','TXN-PAY-0001'),
(2,'2025-02-16',8500.00,'NETBANKING','TXN-PAY-0002'),
(3,'2024-06-02',22000.00,'CARD','TXN-PAY-0003'),
(4,'2025-03-02',8500.00,'UPI','TXN-PAY-0004'),
(5,'2025-01-11',22000.00,'CASH','TXN-PAY-0005'),
(6,'2025-04-02',18000.00,'CHEQUE','TXN-PAY-0006'),
(7,'2025-05-02',22000.00,'UPI','TXN-PAY-0007'),
(9,'2025-01-16',15000.00,'NETBANKING','TXN-PAY-0008'),
(10,'2025-06-02',4500.00,'UPI','TXN-PAY-0009'),
(11,'2024-01-02',22000.00,'CARD','TXN-PAY-0010'),
(13,'2025-03-16',18000.00,'CHEQUE','TXN-PAY-0011'),
(15,'2025-01-02',22000.00,'UPI','TXN-PAY-0012');

-- CLAIMS (15)
INSERT INTO claim (claim_number, policy_id, dependant_id, hospital_id, claim_date, claimed_amount, status, submitted_by) VALUES
('CLM-2025-0001',1,2,1,'2025-03-10',85000.00,'SUBMITTED',2),
('CLM-2025-0002',2,NULL,1,'2025-05-20',45000.00,'SUBMITTED',2),
('CLM-2025-0003',4,NULL,3,'2025-06-15',120000.00,'SUBMITTED',3),
('CLM-2025-0004',5,5,2,'2025-04-05',60000.00,'SUBMITTED',2),
('CLM-2025-0005',6,NULL,4,'2025-05-01',30000.00,'SUBMITTED',3),
('CLM-2025-0006',7,6,5,'2025-07-10',75000.00,'SUBMITTED',2),
('CLM-2025-0007',8,NULL,1,'2025-04-20',20000.00,'SUBMITTED',2),
('CLM-2025-0008',9,NULL,6,'2025-03-05',250000.00,'SUBMITTED',3),
('CLM-2025-0009',10,NULL,8,'2025-08-15',15000.00,'SUBMITTED',2),
('CLM-2025-0010',12,NULL,7,'2025-09-01',40000.00,'SUBMITTED',2),
('CLM-2025-0011',13,NULL,2,'2025-05-20',55000.00,'SUBMITTED',3),
('CLM-2025-0012',14,NULL,8,'2025-09-10',12000.00,'SUBMITTED',2),
('CLM-2025-0013',1,NULL,2,'2025-07-15',30000.00,'SUBMITTED',2),
('CLM-2025-0014',7,7,6,'2025-08-01',45000.00,'SUBMITTED',2),
('CLM-2025-0015',9,NULL,1,'2025-10-01',60000.00,'SUBMITTED',3);

-- TREATMENTS (one per claim)
INSERT INTO treatment (claim_id, treatment_name, diagnosis, admission_date, discharge_date, treatment_cost) VALUES
(1,'Appendectomy','Acute Appendicitis','2025-03-08','2025-03-11',85000.00),
(2,'Dengue Management','Dengue Fever','2025-05-18','2025-05-21',45000.00),
(3,'Knee Replacement','Osteoarthritis','2025-06-10','2025-06-16',120000.00),
(4,'Pediatric Fever Care','Viral Fever','2025-04-03','2025-04-06',60000.00),
(5,'Cataract Surgery','Cataract','2025-04-29','2025-05-01',30000.00),
(6,'Gallbladder Removal','Cholelithiasis','2025-07-08','2025-07-11',75000.00),
(7,'Appendectomy','Acute Appendicitis','2025-04-18','2025-04-21',20000.00),
(8,'Cardiac Bypass Surgery','Coronary Artery Disease','2025-03-01','2025-03-08',250000.00),
(9,'Minor Fracture Treatment','Fractured Wrist','2025-08-13','2025-08-16',15000.00),
(10,'Hernia Repair','Inguinal Hernia','2025-08-29','2025-09-02',40000.00),
(11,'Cataract Surgery','Cataract','2025-05-18','2025-05-21',55000.00),
(12,'Dermatology Treatment','Severe Skin Infection','2025-09-08','2025-09-11',12000.00),
(13,'Physiotherapy Course','Post-Surgical Rehab','2025-07-13','2025-07-16',30000.00),
(14,'Tonsillectomy','Chronic Tonsillitis','2025-07-30','2025-08-02',45000.00),
(15,'Angioplasty','Coronary Artery Blockage','2025-09-28','2025-10-03',60000.00);

-- CLAIM DOCUMENTS
INSERT INTO claim_document (claim_id, document_type, file_reference, upload_date) VALUES
(1,'DISCHARGE_SUMMARY','/docs/clm1_discharge.pdf','2025-03-12'),
(1,'BILL','/docs/clm1_bill.pdf','2025-03-12'),
(2,'PRESCRIPTION','/docs/clm2_prescription.pdf','2025-05-22'),
(3,'DISCHARGE_SUMMARY','/docs/clm3_discharge.pdf','2025-06-17'),
(4,'BILL','/docs/clm4_bill.pdf','2025-04-07'),
(5,'LAB_REPORT','/docs/clm5_lab.pdf','2025-05-02'),
(6,'DISCHARGE_SUMMARY','/docs/clm6_discharge.pdf','2025-07-12'),
(6,'BILL','/docs/clm6_bill.pdf','2025-07-12'),
(7,'BILL','/docs/clm7_bill.pdf','2025-04-22'),
(8,'DISCHARGE_SUMMARY','/docs/clm8_discharge.pdf','2025-03-10'),
(8,'LAB_REPORT','/docs/clm8_lab.pdf','2025-03-10'),
(9,'PRESCRIPTION','/docs/clm9_prescription.pdf','2025-08-17'),
(10,'BILL','/docs/clm10_bill.pdf','2025-09-03'),
(11,'DISCHARGE_SUMMARY','/docs/clm11_discharge.pdf','2025-05-22'),
(12,'LAB_REPORT','/docs/clm12_lab.pdf','2025-09-12'),
(13,'BILL','/docs/clm13_bill.pdf','2025-07-17'),
(14,'DISCHARGE_SUMMARY','/docs/clm14_discharge.pdf','2025-08-03'),
(15,'BILL','/docs/clm15_bill.pdf','2025-10-04');

-- ASSESSMENTS (claims 3, 9 and 15 intentionally left un-assessed to
-- demonstrate the "pending claims" report)
INSERT INTO assessment (claim_id, assessor_id, assessment_date, assessed_amount, remarks) VALUES
(1,4,'2025-03-14',80000.00,'Minor deduction for non-medical items'),
(2,4,'2025-05-23',45000.00,'Approved as claimed'),
(4,5,'2025-04-08',55000.00,'Room rent capped as per plan terms'),
(5,5,'2025-05-03',30000.00,'Approved as claimed'),
(6,4,'2025-07-13',72000.00,'Minor deduction for consumables'),
(7,5,'2025-04-23',20000.00,'Approved as claimed'),
(8,4,'2025-03-11',225000.00,'Deduction for non-network hospital surcharge'),
(10,5,'2025-09-04',40000.00,'Approved as claimed'),
(11,4,'2025-05-23',52000.00,'Minor deduction on consumables'),
(12,5,'2025-09-13',12000.00,'Excluded under cosmetic dermatology clause'),
(13,4,'2025-07-18',30000.00,'Approved as claimed'),
(14,5,'2025-08-04',45000.00,'Approved as claimed');

-- DECISIONS (mirrors the assessed claims above; one REJECTED to keep the
-- approval-rate report meaningful rather than a flat 100%)
INSERT INTO decision (claim_id, decision_date, decision_status, approved_amount, decided_by) VALUES
(1,'2025-03-15','PARTIALLY_APPROVED',80000.00,1),
(2,'2025-05-24','APPROVED',45000.00,1),
(4,'2025-04-09','PARTIALLY_APPROVED',55000.00,1),
(5,'2025-05-04','APPROVED',30000.00,1),
(6,'2025-07-14','APPROVED',72000.00,1),
(7,'2025-04-24','APPROVED',20000.00,1),
(8,'2025-03-12','PARTIALLY_APPROVED',220000.00,1),
(10,'2025-09-05','APPROVED',40000.00,1),
(11,'2025-05-24','PARTIALLY_APPROVED',50000.00,1),
(12,'2025-09-14','REJECTED',0.00,1),
(13,'2025-07-19','APPROVED',30000.00,1),
(14,'2025-08-05','APPROVED',45000.00,1);

-- SETTLEMENTS (7 of the 11 approved/partially-approved claims settled;
-- claims 1, 4, 8 and 11 left approved-but-unsettled on purpose)
INSERT INTO settlement (claim_id, settlement_date, settled_amount, settlement_mode, transaction_ref) VALUES
(2,'2025-05-26',45000.00,'NEFT','TXN-SETL-0001'),
(5,'2025-05-06',30000.00,'UPI','TXN-SETL-0002'),
(6,'2025-07-16',72000.00,'NEFT','TXN-SETL-0003'),
(7,'2025-04-26',20000.00,'UPI','TXN-SETL-0004'),
(10,'2025-09-07',40000.00,'NEFT','TXN-SETL-0005'),
(13,'2025-07-21',30000.00,'CHEQUE','TXN-SETL-0006'),
(14,'2025-08-07',45000.00,'UPI','TXN-SETL-0007');

-- APPEALS (3)
INSERT INTO appeal (claim_id, appeal_date, reason, appeal_status, resolution_date, resolution_remarks) VALUES
(1,'2025-03-18','Customer disputes the deduction on partial approval','PENDING',NULL,NULL),
(8,'2025-03-15','Customer disputes non-network surcharge deduction','PENDING',NULL,NULL),
(12,'2025-09-16','Customer contests rejection under cosmetic exclusion clause','RESOLVED','2025-09-25','Reviewed by senior assessor; original rejection upheld per policy exclusions');
