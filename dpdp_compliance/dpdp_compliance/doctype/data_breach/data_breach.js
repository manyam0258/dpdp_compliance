// Copyright (c) 2026, manyam surendhranath and contributors
// For license information, please see license.txt

frappe.ui.form.on("Data Breach", {
    refresh(frm) {
        // 72-hour deadline warning
        if (frm.doc.hours_remaining && frm.doc.hours_remaining <= 12
            && frm.doc.status !== "Reported to DPB" && frm.doc.status !== "Closed") {
            frm.dashboard.set_headline(
                __("🚨 CRITICAL: Only {0}h remaining to report to DPB!", [
                    Math.round(frm.doc.hours_remaining * 10) / 10,
                ]),
                "red"
            );
        }

        // Quick action buttons
        if (frm.doc.status === "Detected" && !frm.doc.__islocal) {
            frm.add_custom_button(__("Mark as Contained"), function () {
                frm.set_value("status", "Contained");
                frm.save();
            }, __("Actions"));
        }

        if (frm.doc.status === "Contained" && !frm.doc.__islocal) {
            frm.add_custom_button(__("Mark Reported to DPB"), function () {
                frm.set_value("status", "Reported to DPB");
                frm.set_value("reported_to_dpb_on", frappe.datetime.now_datetime());
                frm.save();
            }, __("Actions"));
        }
    },
});
