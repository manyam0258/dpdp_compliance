// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Privacy Notice", {
    refresh(frm) {
        if (frm.doc.is_active && frm.doc.docstatus === 1) {
            frm.set_intro(
                __("This is the currently active Privacy Notice (v{0}).", [frm.doc.version]),
                "green"
            );
        }
    },
});
