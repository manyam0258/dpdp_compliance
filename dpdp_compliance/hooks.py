app_name = "dpdp_compliance"
app_title = "DPDP Compliance"
app_publisher = "surendhranath"
app_description = "Digital Personal Data Protect Act"
app_email = "manyam.surendhranath@gmail.com"
app_license = "gpl-3.0"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "dpdp_compliance",
# 		"logo": "/assets/dpdp_compliance/logo.png",
# 		"title": "DPDP Compliance",
# 		"route": "/dpdp_compliance",
# 		"has_permission": "dpdp_compliance.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/dpdp_compliance/css/dpdp_compliance.css"
# app_include_js = "/assets/dpdp_compliance/js/dpdp_compliance.js"

# include js, css files in header of web template
# web_include_css = "/assets/dpdp_compliance/css/dpdp_compliance.css"
# web_include_js = "/assets/dpdp_compliance/js/dpdp_compliance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "dpdp_compliance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "dpdp_compliance/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "dpdp_compliance.utils.jinja_methods",
# 	"filters": "dpdp_compliance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "dpdp_compliance.install.before_install"
# after_install = "dpdp_compliance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "dpdp_compliance.uninstall.before_uninstall"
# after_uninstall = "dpdp_compliance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "dpdp_compliance.utils.before_app_install"
# after_app_install = "dpdp_compliance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "dpdp_compliance.utils.before_app_uninstall"
# after_app_uninstall = "dpdp_compliance.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "dpdp_compliance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "User": {
        "after_insert": "dpdp_compliance.consent_management.consent_controller.process_signup_consent"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"dpdp_compliance.tasks.all"
# 	],
# 	"daily": [
# 		"dpdp_compliance.tasks.daily"
# 	],
# 	"hourly": [
# 		"dpdp_compliance.tasks.hourly"
# 	],
# 	"weekly": [
# 		"dpdp_compliance.tasks.weekly"
# 	],
# 	"monthly": [
# 		"dpdp_compliance.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "dpdp_compliance.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "dpdp_compliance.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "dpdp_compliance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "dpdp_compliance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["dpdp_compliance.utils.before_request"]
# after_request = ["dpdp_compliance.utils.after_request"]

# Job Events
# ----------
# before_job = ["dpdp_compliance.utils.before_job"]
# after_job = ["dpdp_compliance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"dpdp_compliance.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
