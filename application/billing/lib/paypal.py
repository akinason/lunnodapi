from application.billing.lib.base import Base 


class Paypal(Base):

    def __init__(self):
        super().__init__()
        self.implements_callback = True 
        self.implements_verification = True 
        self.internal_name = "PAYPAL"

    def verify(self, transaction_id):
        return super().verify(transaction_id)


    def parse_callback(self, request_data):
        return super().parse_callback(request_data)

    