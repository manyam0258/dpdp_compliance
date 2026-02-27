// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Data Asset", {
    refresh(frm) {
        if (frm.doc.classification === "Sensitive Personal Data" && !frm.doc.is_encrypted) {
            frm.dashboard.set_headline(
                __("⚠️ Sensitive Personal Data should be encrypted at rest."),
                "orange"
            );
        }
    },
});
