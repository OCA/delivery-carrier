By default, automatic packaging is enabled.

You can disable it in Inventory / Configuration / Settings, by searching "Default Packages".

When active, pickings without assigned packages will be grouped into a single one for shipping. This ensures compatibility with connectors that require at least one package to generate labels or tracking references.

> **NOTE:** If the Number of Packages field is manually set but no real packages are defined, this feature overrides it and creates only one package.
This may cause confusion when relying solely on that field instead of using Odoo’s standard package objects.
