import hashlib 

from application.billing.lib.base import Base
from application.models.billing import PaymentGateway 
from config import config 


class Monetbil(Base):

    def __init__(self):
        super().__init__()
        self.implements_callback = True 
        self.internal_name = "MONETBIL"
        self.callback_url = self.get_callback_url()  # Make sure this is placed after self.internal_name, as the name is part of the url

    def verify(self, transaction_id):
        return super().verify(transaction_id)

    def parse_callback(self, request_data):
        response = super().parse_callback(request_data)
        # message = request_data.get('message')
        status = request_data.get('status')
        internal_reference = request_data.get('payment_ref')
        # amount = request_data.get('amount')
        # currency = request_data.get('currency')
        external_reference = request_data.get('transaction_id')

        response["internal_reference"] = internal_reference
        response["data"] = request_data 
        response["external_reference"] = external_reference

        if status == "success":
            response["success"] = True 
        
        if not "sign" in request_data.keys():
            response["success"] = False 
        
        return response

    def _check_signature(self, request_data):
        sign = request_data.pop("sign")
        data = request_data 
        pg = PaymentGateway.get_payment_gateway_using_internal_name(self.internal_name)
        pg.decrypt_params()
        params = "".join(request_data.values())
        params = pg.params.get("values").get("service_secret") + params 
        signature = hashlib.md5(params).hexdigest()
        return signature == sign 
    
   

