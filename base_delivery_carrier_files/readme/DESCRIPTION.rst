Base module for creation of carrier files (La Poste, TNT Express Shipper, ...).
Files are exported as text (csv, ...).
It contains :
- the base structure to handle the export of files on Delivery Orders
- an API to ease the generation of the files for the developers in sub-modules.

The delivery orders can be grouped in one file or be exported each one in a separate file. The files can be generated automatically on the shipment of a Delivery Order or from a manual action. They are exported to a defined path or in a document directory of your choice if the "document" module is installed.

A generic carrier file is included in the module. It can also be used as a basis to create your own sub-module.

Sub-modules already exist to generate file according to specs of :
 - La Poste (France) : delivery_carrier_file_laposte
 - TNT Express Shipper (France) : delivery_carrier_file_tnt
 - Make your own ! Look at the code of the modules above,
   it's trivial to create a sub-module for a carrier.
