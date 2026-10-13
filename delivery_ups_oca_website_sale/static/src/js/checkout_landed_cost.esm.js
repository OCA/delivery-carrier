/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteSaleCheckout.include({
    /**
     * Update the UPS Duties, Taxes & Fees summary row alongside the standard
     * cart summary values.
     *
     * @override
     */
    _updateCartSummary(result) {
        this._super(...arguments);
        const row = document.querySelector("#order_ups_landed_cost");
        if (!row) {
            return;
        }
        const amount = result.ups_landed_cost;
        if (amount) {
            const field = row.querySelector(".monetary_field");
            if (field) {
                field.innerHTML = amount;
            }
            row.classList.remove("d-none");
        } else {
            row.classList.add("d-none");
        }
    },
});
