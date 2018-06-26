To configure this module, you need to:

* Set the **carrier config**:

 * Go to *Settings/Configuration/Carriers*
 * Create new record:

  * Seur have to provide the integration, accounting and franchise codes and username/password
  * The format expected for **VAT** field is AXXXXXXXX and not ESAXXXXXXX
  * The **file type** is 'txt' if you use a Zebra printer

* Set the **delivery method**:

 * Go to *Warehouse/Configuratio/Delivery Methods*
 * Create new record:

  * Set SEUR as *type*
  * In the *SEUR Config*, set the config created previously
  * The *Service and Product Codes* will be the default options but you will be able to choose others in the stock picking. You have some info about Seur services and products here: http://www.seur.com/contenido/oferta-general/transporte-nacional/urgencia.html
  * For *Transport Company* just create a partner for Seur
  * For *Delivery Product* select or create a product for shipping costs
