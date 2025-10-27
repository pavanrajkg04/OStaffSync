import duckdb
import uuid
from datetime import datetime, date

# --------------------------------------------------------
# HRMS + TASK MANAGEMENT DATABASE SCHEMA (DuckDB)
# --------------------------------------------------------

# Connect to DuckDB (creates file if not exists)
con = duckdb.connect("hrms.duckdb")

# ----------------------------
# 1. Core HRMS Tables
# ----------------------------

# Tenants table (represents companies)
con.execute("""
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    domain TEXT,
    plan TEXT DEFAULT 'basic',
    created_at TIMESTAMP DEFAULT NOW()
)
""")

# Users table (employees)
con.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    company_name TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT,
    status TEXT DEFAULT 'active',
    date_joined TIMESTAMP DEFAULT NOW()
)
""")

# Departments table
con.execute("""
CREATE TABLE IF NOT EXISTS departments (
    dept_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    name TEXT,
    manager_id TEXT REFERENCES users(user_id)
)
""")

# Attendance table
con.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    date DATE NOT NULL,
    status TEXT CHECK(status IN ('present', 'absent', 'Half day', 'leave', 'remote')),
    check_in TIMESTAMP,
    check_out TIMESTAMP
)
""")

# Leaves table
con.execute("""
CREATE TABLE IF NOT EXISTS leaves (
    leave_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    type TEXT,
    start_date DATE,
    end_date DATE,
    status TEXT CHECK(status IN ('pending', 'approved', 'rejected')),
    requested_at TIMESTAMP DEFAULT NOW()
)
""")

# Payroll table
con.execute("""
CREATE TABLE IF NOT EXISTS payroll (
    payroll_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    month TEXT,
    gross_salary DOUBLE,
    deductions DOUBLE,
    net_salary DOUBLE,
    processed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, user_id, month)
)
""")

# Logins table
con.execute("""
CREATE TABLE IF NOT EXISTS logins (
    login_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    last_login TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    account_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

# Performance table
con.execute("""
CREATE TABLE IF NOT EXISTS performance (
    performance_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    kpi_name TEXT,
    score DOUBLE,
    review_date DATE,
    notes TEXT
)
""")

# Recruitment table
con.execute("""
CREATE TABLE IF NOT EXISTS recruitment (
    candidate_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    name TEXT,
    email TEXT,
    position TEXT,
    status TEXT CHECK(status IN ('applied', 'interview', 'hired', 'rejected')),
    applied_at TIMESTAMP DEFAULT NOW()
)
""")

# ----------------------------
# 2. Task Management Module
# ----------------------------

# Tasks table (core)
con.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    created_by TEXT NOT NULL REFERENCES users(user_id),
    assigned_to TEXT REFERENCES users(user_id),
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('todo', 'in_progress', 'review', 'done')) DEFAULT 'todo',
    due_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)
""")

# Task comments (for discussions/chat)
con.execute("""
CREATE TABLE IF NOT EXISTS task_comments (
    comment_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

# Subtasks (smaller units of work)
con.execute("""
CREATE TABLE IF NOT EXISTS subtasks (
    subtask_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    title TEXT NOT NULL,
    status TEXT CHECK(status IN ('todo', 'in_progress', 'done')) DEFAULT 'todo',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
)
""")

# Task attachments (optional file uploads)
con.execute("""
CREATE TABLE IF NOT EXISTS task_attachments (
    attachment_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    uploaded_by TEXT REFERENCES users(user_id),
    file_name TEXT,
    file_path TEXT,
    uploaded_at TIMESTAMP DEFAULT NOW()
)
""")

# Activity log (optional change tracking)
con.execute("""
CREATE TABLE IF NOT EXISTS activity_log (
    log_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT REFERENCES users(user_id),
    task_id TEXT REFERENCES tasks(task_id),
    action TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)
""")

# ----------------------------
# 3. Confirmation
# ----------------------------

print("\n✅ DuckDB HRMS setup complete with Task Management module integrated.")
con.close()
