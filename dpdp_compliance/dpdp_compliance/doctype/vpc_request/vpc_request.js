// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("VPC Request", {
    refresh(frm) {
        if (frm.doc.status === "Pending") {
            frm.set_intro(
                __("Waiting for parental verification."),
                "orange"
            );
        }
    },
});
