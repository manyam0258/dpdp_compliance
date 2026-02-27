---
name: frappe-assistant-mcp-devtool
description: >
  Use this skill for leveraging Frappe Assistant Core App's MCP (Model Context Protocol)
  features to ACCELERATE DEVELOPMENT of the dpdp_compliance custom app. This is about using
  Frappe Assistant as an AI development co-pilot — not integrating with it. Triggers include:
  using MCP to scaffold DocTypes, generate migrations, write hooks, debug errors, generate
  test data, run bench commands via AI, query the Frappe database through natural language,
  or use the AI assistant to inspect and build Frappe app components. Always use this skill
  when the user asks "how do I use Frappe Assistant to build X", "can I use MCP to scaffold",
  "use AI to generate this DocType", or mentions using Frappe Assistant during development.
  This skill dramatically reduces development time for the DPDP compliance app.
compatibility:
  frappe_version: ">=16.0"
  requires: [frappe_assistant_core]
---

# Frappe Assistant MCP as a Development Accelerator

## Core Concept

Frappe Assistant Core App exposes MCP tools that let an AI (Claude, running via the MCP server)
interact directly with your Frappe instance. This means during development of `dpdp_compliance`,
you can instruct the AI assistant to:

- Scaffold complete DocTypes with fields, permissions, and controllers
- Query live DB to understand data shape
- Run bench commands (migrate, build, clear-cache)
- Inspect existing DocType schemas
- Generate test data for QA
- Debug errors by reading Error Logs directly

**The MCP server runs inside your Frappe bench. Claude connects via the MCP protocol.**

---

## 1. Setting Up Frappe Assistant MCP for Development

```bash
# Install Frappe Assistant Core App
cd /path/to/frappe-bench
bench get-app frappe_assistant  # or from GitHub
bench --site your-site.local install-app frappe_assistant

# Configure MCP server (exposes Frappe to Claude/AI)
bench --site your-site.local frappe-assistant setup-mcp

# The MCP server is now available at:
# http://localhost:8000/api/method/frappe_assistant.mcp.server
# or via stdio transport for Claude Desktop / Claude Code
```

### Claude Desktop / Claude Code MCP Config
```json
// ~/.claude/claude_desktop_config.json  (for Claude Desktop)
{
  "mcpServers": {
    "frappe-dev": {
      "command": "bench",
      "args": ["--site", "your-site.local", "frappe-assistant", "mcp-stdio"],
      "cwd": "/path/to/frappe-bench"
    }
  }
}
```

---

## 2. MCP Tools Available for Development

Frappe Assistant Core exposes these tools to the AI during development:

### DocType & Schema Tools
```
frappe_get_doctype_schema    → Read any DocType's field definitions
frappe_create_doctype        → Create a new DocType with fields
frappe_update_doctype        → Add/modify fields on existing DocType
frappe_get_all_doctypes      → List all installed DocTypes
```

### Database Query Tools
```
frappe_db_query      → Execute frappe.get_all() with filters/fields
frappe_db_sql        → Run raw SQL (read-only in production)
frappe_db_count      → Count records matching a filter
frappe_get_doc       → Fetch a specific document by name
```

### Development Tools
```
frappe_run_bench_cmd     → Execute bench commands (migrate, build, clear-cache)
frappe_read_error_log    → Read latest Error Log entries
frappe_read_server_log   → Read bench server logs
frappe_execute_python    → Run Python in Frappe context (like bench console)
frappe_read_file         → Read app source files
frappe_write_file        → Write/create app source files
```

### Testing Tools
```
frappe_create_test_data  → Insert test records (DocType, values)
frappe_delete_test_data  → Clean up test records
frappe_run_tests         → Execute Python unit tests
```

---

## 3. Development Workflow Using MCP

### Workflow: Build a New DocType via AI

Instead of manually creating JSON schemas, instruct the AI:

```
Developer → AI: "Create the Consent Purpose DocType with fields:
  - purpose_name (Data, required, unique)
  - description (Small Text)
  - is_mandatory (Check, default 0)
  - validity_days (Int, default 365)
  - legal_basis (Select: Consent/Legal Obligation/Legitimate Interest)
  - is_active (Check, default 1)
  Make it submittable with track_changes enabled.
  DPO role: Read/Write/Submit. System Manager: all permissions."

AI → [calls frappe_create_doctype]
  → Creates doctype JSON in app directory
  → [calls frappe_run_bench_cmd: migrate]
  → DocType is live in the system
```

### Workflow: Debug a Hook Not Firing

```
Developer → AI: "My process_signup_consent hook isn't firing on User creation.
  Show me the hooks.py and check if it's registered correctly."

AI → [calls frappe_read_file: dpdp_compliance/hooks.py]
  → Reviews doc_events registration
  → [calls frappe_read_error_log: last 10 entries]
  → Finds the error / identifies the issue
  → [calls frappe_write_file: corrected hooks.py]
  → [calls frappe_run_bench_cmd: bench --site x.local migrate]
  → [calls frappe_run_bench_cmd: bench --site x.local clear-cache]
  → Confirms fix
```

### Workflow: Generate Test Consent Data

```
Developer → AI: "Create 50 test Consent Log records for user test@example.com
  across purposes: Email Marketing, Analytics, Core Service.
  Mix statuses: 30 Granted, 15 Withdrawn, 5 Expired."

AI → [calls frappe_create_test_data] x 50
  → Inserts records with realistic timestamps
  → Confirms: "50 Consent Log records created."
```

### Workflow: Query Live DB During Development

```
Developer → AI: "How many users have given consent for Marketing
  but not for Analytics? Show me the breakdown."

AI → [calls frappe_db_sql:
  SELECT u.email, 
         SUM(CASE WHEN cl.purpose = 'marketing' THEN 1 ELSE 0 END) as marketing,
         SUM(CASE WHEN cl.purpose = 'analytics' THEN 1 ELSE 0 END) as analytics
  FROM `tabConsent Log` cl
  JOIN `tabUser` u ON cl.user = u.name
  WHERE cl.status = 'Granted' AND cl.docstatus = 1
  GROUP BY u.email
  HAVING marketing = 1 AND analytics = 0
  LIMIT 10
]
→ Returns real data from your development site
```

### Workflow: Write and Test an API Endpoint

```
Developer → AI: "Write a whitelisted API endpoint 'get_dpo_dashboard' in api.py
  that returns: consent_coverage_pct, open_dsr_count, open_breach_count.
  Then test it by calling it and showing the response."

AI → [calls frappe_write_file: dpdp_compliance/api.py] (adds the function)
  → [calls frappe_run_bench_cmd: bench build]
  → [calls frappe_execute_python:
      import frappe; frappe.connect(); 
      from dpdp_compliance.api import get_dpo_dashboard;
      print(get_dpo_dashboard())
    ]
  → Returns live result from the function
```

---

## 4. Useful MCP Prompts for DPDP App Development

Copy-paste these prompts into Frappe Assistant during development:

### Scaffold All DocTypes at Once
```
Using Frappe Assistant MCP, create all DPDP compliance DocTypes in one go:
1. Consent Purpose (master, submittable)
2. Privacy Notice (master, submittable, track_changes)
3. Consent Log (transaction, submittable, immutable — no edit/delete after submit)
4. Data Subject Request (transaction, submittable, track_changes, SLA field)
5. Data Breach (transaction, submittable, DPO-only permissions)
6. Data Asset (master)
7. Data Processor (master)
8. Retention Policy (master)
9. DPDP Settings (single doctype — one record)

For each: create the JSON schema file, Python controller stub, and JS client script.
Then run bench migrate to apply all at once.
```

### Inspect Existing ERPNext Schema
```
Using frappe_get_doctype_schema, show me all fields in the User, Customer, 
Employee, and Contact DocTypes that contain personal data (name, email, phone, 
DOB, address). I need to build the Data Asset inventory from this.
```

### Auto-Generate Migrations
```
I need to add custom fields to the User DocType:
- date_of_birth (Date)
- is_minor (Check, read_only)
- guardian_email (Data)
- vpc_status (Select: Not Required/Pending/Verified/Expired)
- account_status (Select: Active/Pending VPC/Suspended)

Create a Custom Field migration file for dpdp_compliance app and run it.
Do NOT modify the core User DocType JSON — use Custom Fields via fixtures.
```

### Debug Test Failures
```
My test test_consent_capture is failing with:
"frappe.exceptions.DoesNotExistError: Consent Purpose not found"

Read the test file, check if the test setup creates the required Consent Purpose 
fixture, and fix the issue. Show me the corrected test.
```

---

## 5. MCP-Assisted Code Review

Use Frappe Assistant to review your compliance code for correctness:

```
Review dpdp_compliance/consent.py and check:
1. Is the Consent Log always Submitted (not just Inserted)?
2. Is the IP address correctly captured from frappe.local.request_ip?
3. Is there a race condition in create_consent_log for concurrent requests?
4. Are all frappe.db calls parameterized to prevent SQL injection?
5. Is CSRF token handling correct for any custom endpoints?
Suggest fixes for any issues found.
```

---

## 6. MCP for Schema Validation

```python
# Validate that all required DPDP DocTypes exist before app goes live
# Run via: bench --site x.local execute dpdp_compliance.setup.validate_schema

def validate_schema():
    required_doctypes = [
        "Consent Purpose", "Privacy Notice", "Consent Log",
        "Data Subject Request", "Data Breach", "Data Asset",
        "Data Processor", "Retention Policy", "DPDP Settings",
        "Data Nominee", "DPIA Record",
    ]
    missing = [dt for dt in required_doctypes if not frappe.db.exists("DocType", dt)]
    if missing:
        frappe.log_error(f"Missing DocTypes: {missing}", "DPDP Schema Validation")
        raise Exception(f"DPDP Schema incomplete. Missing: {missing}")
    
    # Validate DPDP Settings is populated
    settings = frappe.get_single("DPDP Settings")
    required_settings = ["dpo_email", "company_name", "act_commencement_date"]
    missing_settings = [s for s in required_settings if not settings.get(s)]
    if missing_settings:
        raise Exception(f"DPDP Settings incomplete. Missing: {missing_settings}")
    
    print("✅ DPDP Schema validation passed.")
```

---

## 7. Development Acceleration Summary

| Task | Manual Time | With Frappe Assistant MCP |
|------|-------------|--------------------------|
| Create DocType with 10 fields | 20 min | 2 min (describe → create → migrate) |
| Write API endpoint + test | 30 min | 5 min (describe → write → execute) |
| Debug hook not firing | 45 min | 5 min (read logs → fix → test) |
| Generate 100 test records | 60 min | 2 min (describe → generate) |
| Inspect DB schema | 15 min | 1 min (ask → get schema) |
| Write migration patch | 25 min | 3 min (describe change → write → run) |

---

## Common MCP Development Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `MCP server not responding` | Frappe Assistant not installed/started | `bench install-app frappe_assistant` + `bench start` |
| `Permission denied on frappe_write_file` | App directory is read-only | Check bench user has write access to apps directory |
| `frappe_execute_python returns empty` | Frappe context not initialized | Always include `frappe.connect()` in standalone Python |
| `DocType already exists` after create | DocType was partially created | Use `frappe_update_doctype` instead |
| `bench migrate` fails after AI-generated DocType | Invalid JSON in schema | Ask AI to validate JSON before running migrate |
