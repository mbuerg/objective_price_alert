There are a lot of tutorials online that show how to set a price alert. For instance set the price alert to $20. If price is equal or smaller than $20 send an email. The willingness to pay a certain amount for a product is subjective though. For Person A $20 might be a good price for person B $25 might be a good price. Such decisions are not based on the past prices of a product.

This project consists of the following:
1. A script to get amazon price data and save them in a mysql database
2. A script that pulls this data from the database and decides if the current value of the time series is significantly low

The "objective_price_example.py" script shows an example of the logic. It basically works like this:
If price or change in price or change in change in price are low compared to it´s former values the price is objectively low. Think of it as derivatives just in a discrete manner.
In order to achieve this the time series is differentiated until stationarity is achieved (max order 2). Then Tschebyscheff´s inequality is used to determine, if the current values are low.

The example in the script is significantly low in it´s price and the first order derivative and can thus be seen as "objectively low".

![Figure 2023-06-11 112341](https://github.com/mbuerg/objective_price_alert/assets/106337257/0248b14e-45f2-4c6c-902f-c61de511788a)

Thus an email is sent.

The script also has a real world example with Bitcoin. The current price is not significantly low. In this case no email is sent.

![btc](https://github.com/mbuerg/objective_price_alert/assets/106337257/6e24cbef-e92d-47f6-b68f-bae5abf86fae)
