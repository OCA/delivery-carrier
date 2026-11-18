At the moment, the module only allows to define the field
prod_environment by defining a \[delivery_carrier\] with
prod_environment key as follows:

Restrict usage of prod environment:

    [delivery_carrier]
    prod_environment=False

Force usage of prod environment:

    [delivery_carrier]
    prod_environment=False

If the key is not set, the user will still be able to switch the value.
