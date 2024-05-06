\*\* How does it works ? \*\*

In picking UI a button "Send to shipper" trigger label generation
calling send_to_shipper() in models/stock.picking.py

\*\* How to implement my own carrier ? \*\*

Define a method {carrier}\_send_shipping() which is called by
\_send_shipping native method. Make it return a list of dict of this
form :

``` python
{
    "exact_price": price,
    "tracking_number": 'number'
    "labels": [{
        "package_id": package_id,
        "name": filename,
        "datas": file_content (base64),
        "file_type": extension,
        "tracking_number": package_number
    }]
}
```
