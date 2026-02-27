// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Data Subject Request", {
    refresh(frm) {
        // Show SLA warning
        if (frm.doc.hours_until_breach && frm.doc.hours_until_breach < 24
            && frm.doc.status !== "Completed" && frm.doc.status !== "Rejected") {
            frm.dashboard.set_headline(
                __("⚠️ SLA breach in {0} hours — prioritize this request!", [
                    Math.round(frm.doc.hours_until_breach),
                ]),
                "red"
            );
        }

        // Add action buttons based on status
        if (frm.doc.status === "ID Verified" && !frm.doc.__islocal) {
            frm.add_custom_button(__("Process Request"), function () {
                frm.set_value("status", "Processing");
                frm.save();
            }, __("Actions"));
        }
        if (frm.doc.status === "Processing" && !frm.doc.__islocal) {
            frm.add_custom_button(__("Mark Completed"), function () {
                frm.set_value("status", "Completed");
                frm.save();
            }, __("Actions"));
        }
    },
});
