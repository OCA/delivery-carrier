* There's no dummy access key to test API calls so no tests can be performed.
* The test booking and shipping APIs databases aren't connected so it isn't possible to
  perform trackings on test mode.
* Only land shipping is implemented, although the module is prepared for extend to
  air and ocean just considering the mandatory request fields for those methods.
  Some additional adaptations could be needed (e.g.: origin and destination airport,
  port) anyway.
* Only volume is supported as a measure unit and with the limitations of Odoo itself. To
  enjoy a full fledged volume support, install and configure the OCA’s
  `stock_quant_package_dimension` module and its dependencies. The connector is ready to
  make use of their volume computations.
* It’d be needed to extend the method to support Schenker measure units such as  loading
  pieces or pallet space.
* Some more booking features aren’t yet supported although can be extended in the
  future. Some of those, although the complete list would be really extensive:

  * Dangerous goods.
  * Driver pre-advise.
  * Transport temperature.
  * Customs clearance.
  * Cargo insurance.
  * Cash on delivery.
