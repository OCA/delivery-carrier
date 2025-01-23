This module is meant to be used in carrier specific implementation.
In the carrier specific label generation method (delivery.carrier.mycarrier_send_shipping), include the label information in the result with
a dedicated key labels. These labels will then be attached to the picking and isolated in the dedicated attachment table.
{
    "labels": [{
        "name": "mylabel",
        "file": base64_label,
        "file_type": "zpl", # optional
        "package_id": package_id, # optional
    }
    ]
}
