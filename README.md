# Health Insurance Policy & Claims Management System

## Student Details

- Name: <add your name>
- Roll Number: <add your roll number>
- Section: <add your section>
- Course: Database Management Systems

## Project Description

A database management system for managing customers, dependants, policies,
premiums, hospitals, claims, treatments, assessments, decisions, settlements
and appeals at a health insurance provider — covering the full
policy → claim → assessment → settlement → appeal lifecycle.

## Technologies Used

- Python
- Tkinter
- MySQL
- mysql-connector-python

## UI Features

- View records across 15 tables
- Insert new records
- Delete selected records with confirmation
- Select related records using foreign-key dropdowns
- Validate inputs and display database errors

## Folder Guide

```
sql/     MySQL DDL, sample data, and report views (01_schema_mysql.sql,
         02_sample_data.sql, 03_queries_and_views.sql)
app/     Runnable Python application (Tkinter GUI + console front-end)
diagrams/  ER diagram and its generation script
docs/    Setup/demo guides and UI screenshots
```

## Quick Start

Requirements: Python 3.8+ (with Tkinter) and a running MySQL 8.0 server.

```bash
cd app
pip install -r requirements.txt

# 1. edit db_config.ini -> user / password of your MySQL server

# 2. create the database (drops & recreates `hipcms` with sample data)
python setup_database.py

# 3. start the GUI
python gui_app.py
```

Logins: `admin` / `agent1` / `agent2` / `assessor1` / `assessor2`, password
`password` for all. Use **admin** to access Delete.

See `docs/UI_DEMO_GUIDE.md` for a step-by-step demo script and
`docs/WORKBENCH_GUIDE.md` for running everything in MySQL Workbench.
