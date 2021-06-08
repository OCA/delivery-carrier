As a requirement you need to install `suds-jurko` library. It will fail with the
latest and outdated version of `suds`.
https://pypi.python.org/pypi/suds-jurko/0.6


Furthermore, if you want to use the integration server of Postlogistics
you will have to patch this library with the following patch:

https://fedorahosted.org/suds/attachment/ticket/239/suds_recursion.patch

A copy of this patch is available in `patches` folder of this module.
