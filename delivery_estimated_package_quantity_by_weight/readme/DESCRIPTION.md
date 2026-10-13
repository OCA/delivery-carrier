This module computes the amount of packages a picking out should have
depending on the weight of the products and the limit fixed by the
carrier. It's fully independent of the delivery_package_number module.

A warning is given if the number of packages for the picking out is
above what is considered as the theoretical number of packages for this
picking and the chosen carrier. The goal is to minimize the number of
packages billed by the carrier.

The chosen strategy for the theoretical number of packages is as follow:  
- Split the product_weights into as many items as we have
- Try to fit the heaviest product with the lightest. If it does not work
  then the heaviest should have a box for itself
- While the weight of products does not exceed the limit, continue
  adding products in the same package
