import duckdb
import uuid
from datetime import datetime, date

# Connect to DuckDB (creates file if not exists)
con = duckdb.connect("hrms.duckdb")

# ----------------------------
# 1. Create Tables
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


#Performance table
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

#Recruitment table
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

# Create tasks table
con.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    title TEXT NOT NULL,
    description TEXT,
    created_by TEXT NOT NULL REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT NOW(),
    due_date DATE,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium'
)
""")

# Create task_assignments table
con.execute("""
CREATE TABLE IF NOT EXISTS task_assignments (
    assignment_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    tenant_id TEXT NOT NULL REFERENCES tenants(tenant_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    status TEXT CHECK(status IN ('todo', 'inprogress', 'need_inputs', 'done')) DEFAULT 'todo',
    assigned_at TIMESTAMP DEFAULT NOW()
)
""")

# Create task_status_history table
con.execute("""
CREATE TABLE IF NOT EXISTS task_status_history (
    status_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    previous_status TEXT,
    new_status TEXT CHECK(new_status IN ('todo', 'inprogress', 'need_inputs', 'done')),
    changed_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
)
""")

# Create task_messages table
con.execute("""
CREATE TABLE IF NOT EXISTS task_messages (
    message_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    sender_id TEXT NOT NULL REFERENCES users(user_id),
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW()
)
""")

# Create task_transfers table
con.execute("""
CREATE TABLE IF NOT EXISTS task_transfers (
    transfer_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    from_user_id TEXT NOT NULL REFERENCES users(user_id),
    to_user_id TEXT NOT NULL REFERENCES users(user_id),
    transfer_date TIMESTAMP DEFAULT NOW(),
    notes TEXT
)
""")

print("✅ DB setup complete.")


# ----------------------------
# 2. Insert Sample Data
# ----------------------------

# tenant_id = str(uuid.uuid4())
# company_name = "Acme Corp"

# con.execute(
#     "INSERT INTO tenants VALUES (?, ?, ?, ?, ?)",
#     [tenant_id, company_name, "acme.io", "premium", datetime.now()],
# )

# # Sample users
# user1 = str(uuid.uuid4())
# user2 = str(uuid.uuid4())

# con.execute(
#     "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#     [user1, tenant_id, company_name, "Alice", "alice@acme.io", "Engineer", "active", datetime.now()],
# )
# con.execute(
#     "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#     [user2, tenant_id, company_name, "Bob", "bob@acme.io", "HR", "active", datetime.now()],
# )

# # Sample department
# dept_id = str(uuid.uuid4())
# con.execute("INSERT INTO departments VALUES (?, ?, ?, ?)", [dept_id, tenant_id, "Engineering", user1])

# # Sample attendance
# att_id = str(uuid.uuid4())
# con.execute(
#     "INSERT INTO attendance VALUES (?, ?, ?, ?, ?, ?, ?)",
#     [att_id, tenant_id, user1, date.today(), "present", datetime.now(), None],
# )

# # Sample leave
# leave_id = str(uuid.uuid4())
# con.execute(
#     "INSERT INTO leaves VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#     [leave_id, tenant_id, user2, "Sick Leave", date.today(), date.today(), "approved", datetime.now()],
# )

# # Sample payroll
# payroll_id = str(uuid.uuid4())
# con.execute(
#     "INSERT INTO payroll VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
#     [payroll_id, tenant_id, user1, "2025-10", 5000.0, 500.0, 4500.0, datetime.now()],
# )

# # Sample logins
# login1_id = str(uuid.uuid4())
# login2_id = str(uuid.uuid4())
# con.execute(
#     "INSERT INTO logins VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
#     [login1_id, tenant_id, user1, "alice", "alice123", None, 0, False, datetime.now()],
# )
# con.execute(
#     "INSERT INTO logins VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
#     [login2_id, tenant_id, user2, "bob", "bob123", None, 0, False, datetime.now()],
# )

# # ----------------------------
# # 3. Test Query
# # ----------------------------
# users_df = con.execute(
#     "SELECT name, company_name, email, role FROM users WHERE tenant_id = ?", [tenant_id]
# ).fetch_df()
# print(users_df)

# con.close()

# print("\n✅ DuckDB HRMS setup complete with company_name included.")
