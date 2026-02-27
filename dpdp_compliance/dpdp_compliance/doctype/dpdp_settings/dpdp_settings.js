// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("DPDP Settings", {
    refresh(frm) {
        if (!frm.doc.company_name) {
            frm.set_intro("Please configure your organization's DPDP compliance settings.", "blue");
        }
    },
});
