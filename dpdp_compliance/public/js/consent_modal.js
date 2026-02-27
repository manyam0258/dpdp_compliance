/**
 * DPDP Consent Modal — shown during user signup when consent_modal_enabled is True.
 *
 * Renders active Privacy Notice + Consent Purposes for user acceptance.
 * Passed via User.flags.dpdp_consents for processing in consent.process_signup_consent.
 */
(function () {
    "use strict";

    if (!frappe.boot || !frappe.boot.dpdp_consent_modal_enabled) {
        return;
    }

    // Hook into the signup flow
    $(document).on("page-change", function () {
        if (frappe.get_route_str() === "signup") {
            show_consent_modal_on_signup();
        }
    });

    async function show_consent_modal_on_signup() {
        try {
            const notice = await frappe.call({
                method: "dpdp_compliance.api.get_active_notice",
                args: { language: frappe.boot.lang || "en" },
            });

            if (!notice || !notice.message) return;

            const data = notice.message;
            const purposes = data.purposes || [];
            if (!purposes.length) return;

            // Build modal content
            let purpose_html = purposes
                .map(
                    (p) => `
                <div class="consent-purpose-item" style="margin: 10px 0; padding: 10px; border: 1px solid #d1d8dd; border-radius: 4px;">
                    <label style="display: flex; align-items: flex-start; gap: 8px; cursor: pointer;">
                        <input type="checkbox" class="consent-checkbox"
                            data-purpose="${p.name}"
                            ${p.is_mandatory ? "checked disabled" : ""}
                            style="margin-top: 3px;" />
                        <div>
                            <strong>${frappe.utils.escape_html(p.purpose_name)}</strong>
                            ${p.is_mandatory ? '<span class="badge badge-info" style="margin-left: 6px;">Required</span>' : ""}
                            <p style="margin: 4px 0 0; color: #6c757d; font-size: 0.875em;">
                                ${frappe.utils.escape_html(p.description || "")}
                            </p>
                        </div>
                    </label>
                </div>`
                )
                .join("");

            const d = new frappe.ui.Dialog({
                title: __("Privacy & Consent"),
                fields: [
                    {
                        fieldtype: "HTML",
                        fieldname: "notice_content",
                        options: `
                            <div style="max-height: 300px; overflow-y: auto; padding: 10px; background: #f5f7fa; border-radius: 4px; margin-bottom: 15px;">
                                ${data.content_html}
                            </div>
                            <h6>${__("Consent Choices")}</h6>
                            ${purpose_html}
                        `,
                    },
                ],
                primary_action_label: __("I Agree"),
                primary_action: function () {
                    const consents = [];
                    d.$wrapper.find(".consent-checkbox").each(function () {
                        consents.push({
                            purpose_id: $(this).data("purpose"),
                            accepted: $(this).is(":checked"),
                        });
                    });

                    // Store consents in frappe.boot for the signup handler
                    frappe._dpdp_signup_consents = consents;
                    d.hide();
                },
            });

            d.show();
            d.$wrapper.find(".modal-dialog").css("max-width", "600px");
        } catch (err) {
            console.error("DPDP Consent Modal Error:", err);
        }
    }
})();
