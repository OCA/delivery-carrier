The rendering is configured through system parameters
(Settings > Technical > Parameters > System Parameters):

* ``delivery_zpl_viewer.labelary_url``: Labelary API base URL,
  ``https://api.labelary.com`` by default. Point it to a self-hosted Labelary
  instance to keep the label data inside the company infrastructure.
* ``delivery_zpl_viewer.dpmm``: print density of the labels in
  dots per millimeter (``6``, ``8``, ``12`` or ``24``), ``8`` (203 dpi) by default.
* ``delivery_zpl_viewer.default_size``: label size in inches used
  when the ZPL file does not define it, ``4x6`` by default.
