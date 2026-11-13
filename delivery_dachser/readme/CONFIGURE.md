To configure this module:

1. Go to **Inventory > Configuration > Delivery > Shipping Methods** (or **Sales > Configuration > Shipping Methods**).
2. Open the preconfigured **Dachser European Logistics (targoflex)** shipping method or create a new one with **Provider** = `Dachser`.
3. In the **Dachser Configuration** tab:
   - Enter your **Dachser API Key (X-API-Key)** (or separate **Test API Key** and **Production API Key**) obtained from the [Dachser API Portal](https://api-portal.dachser.com/bi.b2b.portal/api?2).
   - Set your **Dachser Branch ID (forwarder.id)** (e.g. `193`), **Dachser Customer ID (consignor.id)**, **Division** (`T` for European Logistics, `F` for Food Logistics), **Product** (`Y` for targoflex, `Z` for targospeed, `N` for classicline, etc.), and **Term Code / Frankatur** (`031` Free Domicile / CPT, `021` EXW, etc.).
   - Select your **Label Format** (`PDF` or `ZPL`) and **Packaging Type** (`EU` Europallet, `EP` Half Pallet, `KT` Cardboard Box, etc.).
4. In the **Dachser Tariffs & Costs** tab:
   - Choose the **Tariff Calculation Mode** (`API Quotation with Local Tariff Table Fallback`, `Dachser API Only (/rest/v2/quotations)`, or `Local Tariff Table Only (By Zones / Weight / Pallets)`).
   - Configure volumetric conversion factors (`333 kg/m3`, `1850 kg/LDM`), fuel surcharge percentage, tail-lift/notice surcharges, and zone/weight/pallet tariff rules.
