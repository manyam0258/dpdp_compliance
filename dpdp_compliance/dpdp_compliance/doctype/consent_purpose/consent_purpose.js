// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Consent Purpose", {
    refresh(frm) {
        if (frm.doc.is_mandatory) {
            frm.set_intro(
                __("This is a mandatory consent purpose. Users cannot opt out during signup."),
                "blue"
            );
        }
    },
});
