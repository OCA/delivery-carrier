With this module installed, the delivery carrier are
configured in the `server_environment_files` module (which is a module
you should provide, see the documentation of `server_environment` for
more information).

In the configuration file of each environment, you may first use the
section `[carrier_account]`.

Then for each server, you can define additional values or override the
default values with a section named `[carrier_account.resource_name]` where "resource_name" is the name of the server.

Example of config file ::


  [carrier_account]
  # here is the default format
  file_format = 'ZPL'


  [carrier_account.mycarrier]
  name = mycarrier
  account = 587
  password = 123promenons-nous-dans-les-bois456cueillir-des-saucisses


  [carrier_account.mycarrier2]
  name = mycarrier2
  account = 666
  password = wazaaaaa
  file_format = PDF
