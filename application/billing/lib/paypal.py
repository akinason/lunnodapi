from datetime import datetime, timedelta

import arrow 
import requests 
from application import db 
from config import config
from application.billing.lib.base import Base
from application.models.billing import PaymentGateway, BillingTransaction


class Paypal(Base):

    def __init__(self):
        super().__init__()
        self.implements_callback = True 
        self.implements_verification = True 
        self.internal_name = "PAYPAL"
        self.callback_url = self.get_callback_url()
        self._access_token = ""
        self.url = "https://api.sandbox.paypal.com" if config.DEBUG else "https://api.paypal.com"
        self._token_expiry = ""

    def verify(self, transaction_id):
        txn = BillingTransaction.get_transaction_using_id(transaction_id)
        if not txn.response_data:
            return super().verify(transaction_id)
        
        successful, order = self._getOrderDetails(txn.response_data.get("id"))
        if not successful:
            return super().verify(transaction_id)
        
        purchase_units = order.get("purchase_units")
        payments = purchase_units.get("payments")

        if not "captures" in payments.keys():
            return super().verify(transaction_id)

        captures = payments.get("captures")
        if len(captures) == 0:
            return super().verify(transaction_id)
        
        for capture in captures:
            if capture.get("status") == 'COMPLETED':
                return {"success": True, "data": txn.response_data, "transaction_id": transaction_id, "external_reference": txn.response_data.get("id")} 

        return super().verify(transaction_id)


    def parse_callback(self, request_data):
        self._saveWebhookDataToDb(request_data)

        event_type = request_data.get("event_type")
        # we are only interested in the completed captured payment.
        if event_type != "PAYMENT.CAPTURE.COMPLETED":
            return super().parse_callback(request_data)

        links = request_data.get("resource").get("links")
        orderId = ""

        # Extract the order Id from the resource "up" link.
        try:
            for link in links:
                if link.get("rel") == "up":
                    href = link.get("href")
                    orderId = href.split("/")[-1:][0]
        except Exception:
             return super().parse_callback(request_data)

        # Get order details.
        successful, order = self._getOrderDetails(orderId)
   
        if not successful:
            return super().parse_callback(request_data)
        try:
            reference_id = order.get("purchase_units")[0].get("reference_id")
        except Exception:
            return super().parse_callback(request_data)
        
        txn = BillingTransaction.get_transaction_using_reference(reference_id)
        print("Reference ", txn.reference)

        if txn:
            return {"internal_reference": txn.id, "data": request_data, "success": True, "external_reference": order.get("id")}

        return super().parse_callback(request_data)
    

    def _saveWebhookDataToDb(self, data):
        pass 

    def _getOrderDetails(self, orderId):
        endpoint =  f"/v2/checkout/orders/{orderId}"
        status_code, data = self._get(endpoint, {})
        print(data)
        if status_code != 200:
            return False, {}
        else:
            return True, data 

    def _getCapturedPaymentDetails(self, captureId):
        endpoint = f"/v2/payments/captures/{captureId}"
        status_code, data = self._get(endpoint, {})
        print(data)
        if status_code != 200:
            return False, {}
        else:
            return True, data 

    def _setToken(self):
        url = self.url + "/v1/oauth2/token"

        # check if a valid token already exist in the current instance.
        if self._access_token and arrow.get(self._token_expiry) > (arrow.get() + timedelta(minutes=5)):
            return True 

        pg = PaymentGateway.get_payment_gateway_using_internal_name(self.internal_name)
        pg.decrypt_params()
        if pg is None: 
            self._access_token = "" 
            return False 
        
        # check if the token is existing in the db and is still valid.
        if pg.params and "access_token" in pg.params.keys():
            expires_in = arrow.get(pg.params.get("expires_in"))
            if expires_in > (arrow.get() + timedelta(minutes=5)):
                self._access_token = pg.params.get("access_token")
                self._token_expiry = expires_in.datetime
                return True 
        
        # Call PayPal for a new token
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        data = {"grant_type": "client_credentials"}
        r = requests.post(url, headers=headers, data=data, auth=(pg.params.get('client_id'), pg.params.get('client_secret')))
        if r.status_code != 200: 
            self._access_token = ""
            return False 
        
        response = r.json()
        self._access_token = response.get("access_token")
        self._token_expiry = datetime.utcnow() + timedelta(seconds=response.get("expires_in"))
        
        # Update the database with the new token.
        params = pg.params 
        params["access_token"] = self._access_token
        params["expires_in"] = arrow.get(self._token_expiry).for_json()
        pg.params = params
        pg.encrypt_params()
        db.session.add(pg)
        db.session.commit()
        return True 

    def _post(self, endpoint, data):
        url = self.url + endpoint
        self._setToken()

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}"
        }
        response = requests.post(url, data=data, headers=headers)
        status_code = response.status_code
        response_data = response.json()
        return status_code, response_data  

    def _get(self, endpoint, params):
        url = self.url + endpoint 
        self._setToken()
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}"
        }
        response = requests.get(url, params=params, headers=headers)
        status_code = response.status_code
        response_data = response.json()
        return status_code, response_data  

paypal = Paypal()
