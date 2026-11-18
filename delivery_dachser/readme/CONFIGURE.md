To configure this module:

1. Go to **Inventory > Configuration > Delivery > Shipping Methods** (or **Sales > Configuration > Shipping Methods**).
2. Create a new shipping method (or open an existing one) with **Provider** = `Dachser`.
3. In the **Dachser Configuration** tab:
   - Enter your **Dachser Api Key** (`X-API-Key` token from the [Dachser API Portal](https://api-portal.dachser.com/bi.b2b.portal/api?2)) and toggle **Production Environment** as appropriate.
   - Set your **Dachser Branch ID** (e.g. `193`), **Dachser Customer ID**, **Division Code** (`T` for European Logistics, `F` for Food Logistics), **Product Code** (`Y` targoflex, `Z` targospeed, `N` classicline/vengoflex, etc.), and **Term Code** (`031` Free delivered, `021` EXW, etc.).
   - Choose your **Packaging Code**, **Packaging Type** (`stock.package.type`), **Label Format** (`PDF` or `ZPL`), and target eLogistics **Basket** (`sent`, `labelled`, or `imported`).
4. *(Optional)* Install `delivery_price_method` if you wish to define fixed or rule-based local shipping prices instead of querying `POST /rest/v2/quotations`.
