// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Consent Log", {
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.set_intro(
                __("This consent record is immutable and serves as legal evidence under DPDP Act 2023."),
                "blue"
            );
            // Disable all edit controls
            frm.disable_save();
        }
    },
});
