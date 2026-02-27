// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Data Processor", {
    refresh(frm) {
        if (frm.doc.is_active && !frm.doc.dpa_signed) {
            frm.dashboard.set_headline(
                __("⚠️ Active processor without signed DPA — compliance risk."),
                "red"
            );
        }
    },
});
