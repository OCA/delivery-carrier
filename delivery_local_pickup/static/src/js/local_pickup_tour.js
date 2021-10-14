odoo.define("delivery_local_pickup.tour", function(require) {
    "use strict";

    var tour = require("web_tour.tour");

    tour.register(
        "delivery_local_pickup_tour",
        {
            test: true,
        },
        [
            {
                content: "Check local address information",
                trigger: ".address:contains('Local address partner')",
            },
        ]
    );
    return {};
});
