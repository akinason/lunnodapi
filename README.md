The **GET** route returns the list of price lists available. 
- When the user is authenticated, it will return custom and standard price lists. 

- You can as well filter by adding a GET param **"id"** which will return the pricelist with the given pricelist id OR
- You can also filter by passing a GET param named **user** with the user's public id, to get the list of custom user's pricelists.
  