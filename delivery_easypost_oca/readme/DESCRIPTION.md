This module integrates [EasyPost](https://easypost.com) shipping API
with Odoo, providing access to 100+ carriers through a single, unified
interface.

**What is EasyPost?**

EasyPost is a shipping API aggregator that eliminates the need for
separate carrier integrations. Instead of implementing individual APIs
for USPS, UPS, FedEx, DHL, and others, you connect once to EasyPost and
gain access to all supported carriers with pre-negotiated rates.

**Key Features**

- **Automated Rate Calculation**: Get real-time shipping rates from
  multiple carriers and automatically select the lowest rate
- **Label Generation**: Generate and print shipping labels in multiple
  formats (PDF, ZPL, EPL2)
- **Multi-Carrier Support**: Access 100+ carriers including USPS, UPS,
  FedEx, DHL, Canada Post, and regional carriers
- **Shipment Tracking**: Real-time tracking with automatic updates and
  public tracking links
- **Multi-Package Handling**: Support for shipments with multiple
  packages (individual or batch mode)
- **Address Verification**: Automatic address validation to reduce
  delivery errors
- **Multiple Label Formats**: PDF for standard printers, ZPL/EPL2 for
  thermal label printers
- **Test Environment**: Full test mode for development without charges
  or actual shipments
- **Automatic Conversions**: Weight conversion to ounces and currency
  conversion handled automatically

**Benefits of Using EasyPost**

- **Single Integration**: One API connection for all carriers - no need
  to integrate each carrier separately
- **Lowest Rate Selection**: Automatically compares rates from all
  available carriers and selects the cheapest option
- **Pre-Negotiated Rates**: Access to discounted carrier rates through
  EasyPost's volume agreements
- **Reduced Complexity**: Unified API response format regardless of
  carrier
- **Scalability**: Easily add new carriers without code changes
- **Testing Without Risk**: Complete test environment with mock
  shipments

**Technical Architecture**

This module implements a clean, layered architecture:

- **Business Logic Layer** (delivery_carrier.py): Handles Odoo-specific
  logic (orders, pickings, pricing)
- **API Wrapper Layer** (easypost_request.py): Centralizes all EasyPost
  API interactions
- **EasyPost Python SDK** (version 7.15.0): Official EasyPost client
  library
- **Comprehensive Test Suite**: 100% mocked tests with no real API calls
  during testing

**Supported Carriers (via EasyPost)**

USPS, UPS, FedEx, DHL Express, DHL eCommerce, Canada Post, APC Postal,
Asendia, Australia Post, Canpar, Couriers Please, Deutsche Post,
Fastway, Globegistics, Interlink Express, LaserShip, LSO, OnTrac,
Parcelforce, Purolator, Royal Mail, Sendle, StarTrack, and 80+
additional carriers worldwide.

**Use Cases**

- **E-Commerce Stores**: Automatically calculate shipping costs at
  checkout
- **Warehouse Operations**: Generate and print shipping labels for
  outbound orders
- **Multi-Carrier Shipping**: Compare rates across carriers to minimize
  shipping costs
- **International Shipping**: Access to international carriers with
  automatic address verification
- **High-Volume Shipping**: Batch processing for multiple packages in
  single transactions
