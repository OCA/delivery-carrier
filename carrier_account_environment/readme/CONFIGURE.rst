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


As an alternative of `server_environment_files`, there is also a module named `server_environment_data_encryption`
which allow to set the environement dependent values directly in the database, by the user itself.
It will be encrypted, to avoid security issues with secrets, see the documentationn of `server_environment_data_encryption` for more information.
The advantage of setting the environment dependent value directly in the database is that it does not require a developper/odoo administrator to change a carrier account.
