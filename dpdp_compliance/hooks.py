app_name = "dpdp_compliance"
app_title = "DPDP Compliance"
app_publisher = "manyam surendhranath"
app_description = "Digital Personal Data Protection (DPDP) Act 2023 Compliance Tool"
app_email = "surendhra.erpnext@gmail.com"
app_license = "mit"

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
    {
        "name": "dpdp_compliance",
        "logo": "/assets/dpdp_compliance/logo.png",
        "title": "DPDP Compliance",
        "route": "/app/dpdp-settings",
    }
]

# Includes in <head>
# ------------------

# include consent modal JS in desk for signup flow
app_include_js = "/assets/dpdp_compliance/js/consent_modal.js"


# Installation
# ------------

after_install = "dpdp_compliance.setup.after_install"
after_migrate = "dpdp_compliance.setup.after_migrate"


# Permissions
# -----------

permission_query_conditions = {
    "Data Subject Request": "dpdp_compliance.permissions.dsr_permission_query",
    "Consent Log": "dpdp_compliance.permissions.consent_log_permission_query",
    "Nominee Record": "dpdp_compliance.permissions.nominee_permission_query",
}


# Document Events
# ---------------

doc_events = {
    "User": {
        "after_insert": [
            "dpdp_compliance.consent.process_signup_consent",
            "dpdp_compliance.vpc.check_minor_on_signup",
        ],
    },
    "Data Breach": {
        "after_insert": "dpdp_compliance.breach.on_breach_insert",
    },
}


# Scheduled Tasks
# ---------------

scheduler_events = {
    "hourly": [
        "dpdp_compliance.dsr.calculate_sla_hours",
        "dpdp_compliance.breach.calculate_breach_hours",
    ],
    "daily": [
        "dpdp_compliance.consent.expire_stale_consents",
        "dpdp_compliance.retention.run_retention_engine",
    ],
    "weekly": [
        "dpdp_compliance.consent.send_legacy_consent_reminders",
    ],
}


# Website Routes
# ---------------

website_route_rules = [
    {
        "from_route": "/dpdp-portal/<path:app_path>",
        "to_route": "dpdp-portal",
    },
]


# Boot Session
# ---------------

boot_session = "dpdp_compliance.boot.boot_session"


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "Consent Log",
        "filter_by": "user",
        "redact_fields": ["ip_address", "user_agent"],
        "partial": 1,
    },
    {
        "doctype": "Data Subject Request",
        "filter_by": "user",
        "redact_fields": ["description", "resolution_notes"],
        "partial": 1,
    },
    {
        "doctype": "Nominee Record",
        "filter_by": "user",
        "redact_fields": ["nominee_name", "nominee_email"],
        "partial": 1,
    },
    {
        "doctype": "Data Erasure Log",
        "filter_by": "user",
        "partial": 1,
    },
]
# Fixtures
# --------
fixtures = [
    {"doctype": "Desktop Icon", "filters": [["name", "in", ("DPDP Compliance",)]]},
    {"doctype": "Workspace", "filters": [["name", "in", ("DPDP Compliance",)]]},
    {"doctype": "Workspace Sidebar", "filters": [["name", "in", ("DPDP Compliance",)]]},
    {"doctype": "Number Card", "filters": [["module", "=", "DPDP Compliance"]]},
    {"doctype": "Dashboard Chart", "filters": [["module", "=", "DPDP Compliance"]]},
]
