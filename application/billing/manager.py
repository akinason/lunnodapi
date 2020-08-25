from application import db, gm_client
from application.models.billing import BillingTransaction, PaymentGateway
from application.smscenter.manager import Manager as SMSManager 


class Manager:

    def __init__(self):
        self.pg = ""

    def _set_payment_gateway(self, pg_internal_name):
        if pg_internal_name not in PaymentGateway.AVAILABLE_INTERNAL_NAMES:
            return False
        
        if pg_internal_name == PaymentGateway.MONETBIL:
            from application.billing.lib.monetbil import Monetbil 
            self.pg = Monetbil()
        
        if pg_internal_name == PaymentGateway.PAYPAL:
            from application.billing.lib.paypal import Paypal 
            self.pg = Paypal()
        
        if pg_internal_name == PaymentGateway.FLUTTERWAVE:
            from application.billing.lib.flutterwave import Flutterwave 
            self.pg = Flutterwave()
        
        if pg_internal_name == PaymentGateway.CINETPAY:
            from application.billing.lib.cinetpay import CinetPay
            self.pg = CinetPay()
        return True 
    
    def _complete_processing(self, txn):
         # If it's SMS SALES, load the users' account. 
        if txn.transaction_type == BillingTransaction.SMS_SALES:
            mgr = SMSManager()
            res = mgr.sell_sms(dest=txn.smsaccount.public_id, quantity=txn.quantity, user_id=txn.smsaccount.owner_id)

            if res["success"] is False:
                # TODO: reschedule and endsure sms is reloaded into the client's account. 
                return {"success": False, "message": res.get("message")}
            
            txn.is_complete = True 
            db.session.add(txn)
            db.session.commit()

            # send account refill email to client.
            gm_client.submit_job("billing.sms_sales_email", {"transaction_id": txn.id}, background=True, wait_until_complete=False)
            return {"success": True, "message": "Operation Successful."}


    def verify_payment(self, transaction_id):
        txn = BillingTransaction.get_transaction_using_id(transaction_id)
        res = self._set_payment_gateway(txn.payment_gateway.internal_name)
        if res is False: return {"success": False, "message": "Invalid payment gateway %s" % txn.payment_gateway.internal_name}  

        if not self.pg.implements_verification:
            return {"success": False, "message": "%s does not implement verification." % self.pg.internal_name}

        if txn is None or txn.is_complete == True or txn.is_successful:
            # End everything.
            return {"success": False, "message": "Transaction already completed."}

        response = self.pg.verify(transaction_id)
        if response["success"]:
            txn.is_successful = True

            txn.is_verified = True
            txn.verification_data = response.get('data')
            txn.external_reference = response.get("external_reference")
            db.session.add(txn)
            db.session.commit()
            res = self._complete_processing(txn)

        else:
            res = {"success": False, "message": "%s Verificaton failed." % self.pg.internal_name}
        
        return res 

    def parse_callback(self, pg_internal_name, request_data):
        res = self._set_payment_gateway(pg_internal_name)
        if res is False: return {"success": False, "message": "Invalid payment gateway %s" % pg_internal_name}
        
        if not self.pg.implements_callback:
            return {"success": False, "message": "%s does not implement callback." % self.pg.internal_name}

        response = self.pg.parse_callback(request_data)
        reference = response.get('internal_reference')
        txn = BillingTransaction.get_transaction_using_reference(reference)

        if txn is None or txn.is_complete == True or txn.is_successful:
            # End everything.
            return {"success": False, "message": "Invalid reference %s, or transaction already completed." % reference}
        
        if response["success"]:
            txn.is_successful = True

            txn.is_verified = True
            txn.callback_data = response.get('data')
            txn.external_reference = response.get("external_reference")
            db.session.add(txn)
            db.session.commit()

            res = self._complete_processing(txn)
        else:
            res = {"success": False, "message": "%s Verificaton failed." % self.pg.internal_name}
        return res 
    
       

