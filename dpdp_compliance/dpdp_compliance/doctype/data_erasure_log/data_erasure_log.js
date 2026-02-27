// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Data Erasure Log", {
    refresh(frm) {
        frm.set_intro(
            __("This erasure log record is read-only and serves as an audit trail."),
            "blue"
        );
    },
});
