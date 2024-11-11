This module allows to generate SSCC codes for packages automatically.

SSCC codes are explained here: https://www.gs1.org/standards/id-keys/sscc

Typically, a company registers a range of 1000, 10000 or more SSCC codes which
they can then use as barcodes on their packages. These are unique, and once
they run out, new ones are bought.

With this module, you can modify Odoo's package number sequence to pick SSCC
codes from your range, instead of using the standard PACK00001, PACK00002 etc.
