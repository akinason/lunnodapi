import math 
from application import db 
from config import config 
from application.models.smscenter import SMSAccount, SMSTransaction, ShortMessage, sms_status

PLAIN_TEXT_MSG = 0
UNICODE_MSG = 1
PLAIN_TEXT_MSG_LENGTH = 153
UNICODE_MSG_LENGTH = 268

class Manager:

    def __init__(self):
        pass 

    def reload(self, public_id, quantity: int, reverse_transaction=False) -> dict:
        """
        Reloads an SMS account with corresponding number of SMS.
        """
        account = SMSAccount.get_account_using_public_id(public_id)
        if account:
            account.balance = SMSAccount.balance + quantity

            if not reverse_transaction:
                account.historic_total = SMSAccount.historic_total + quantity
            
            if reverse_transaction:
                account.total_sent -= quantity 
            
            db.session.add(account)
            db.session.commit()
            return {"success": True, "balance": account.balance, "account_id": account.id} 
        return {"success": False, "message": "Invalid public id"} 
    
    def remove(self, public_id, quantity: int) -> dict:
        """
        Removes the corresponding number of sms from the account.
        """ 
        account = SMSAccount.get_account_using_public_id(public_id)
        if account:
            if account.balance > quantity:
                account.balance = SMSAccount.balance - quantity
                account.total_sent = SMSAccount.total_sent + quantity 
                db.session.add(account)
                db.session.commit()
                return {"success": True, "balance": account.balance, "account_id": account.id}
            else:
                return {"success": False, "message": "Insufficient balance."}
        
        return {"success": False, "message": "Invalid public id"}
         
    def transfer(self, source, dest, quantity, user_id, description=None) -> dict:
        """
        Transfer's SMS from one account to another.
        :param source: public_id of the account to remove sms from.
        :param dest: public_id of the account to add sms to.
        :param user_id: The destination account user_id, if the destination is not our system, else the source account user_id.
        """
        removed = self.remove(source, quantity)
        if not removed['success']:
            return {"success": False, "message": f"Source account: {removed['message']}"}

        reloaded = self.reload(dest, quantity)
        if not reloaded['success']:
            self.reload(source, quantity, reverse_transaction=True)  # Reload the source account. Hopefully this always works.
            return {"success": False, "message": f"Destination account: {reloaded['message']}"}
      
        # Update transaction table.
        txn = SMSTransaction(source_account_id=removed['account_id'], dest_account_id=reloaded['account_id'], quantity=quantity)
        txn.set_reference()
        txn.description = description if description else f"Transfer from {source} to {dest}"
        txn.user_id = user_id
        txn.source_balance = removed['balance']
        txn.dest_balance = reloaded['balance']
        db.session.add(txn)
        db.session.commit()
        return {"success": True}

    def sell_sms(self, dest, quantity, user_id, description=None):
        """
        Deducts the required quantity of SMS from the SMS_SALES_ACCOUNT Into the destination account. 
        :param dest: The public id of the destination account.
        :param quantity: The number of SMS to reload the account with. 
        """
        source = config.SALES_SMS_ACCOUNT
        res = self.transfer(source=source, dest=dest, quantity=quantity, user_id=user_id, description="SMS Sales")
        return res  

    def _format_mno(self, mno):
        mno_list = str(mno).replace(" ", "").replace("+", "").split(',')
        mno_count = len(mno_list)
        error = None 

        for num in mno_list:
            try:
                int(num)
            except Exception:
                error = f"Invalid Number, {num}"
                break
        
        return mno_count, mno_list, error 

    def _format_msg(self, msg, mno_count, mt):
        error = None 
        LENGTH = 1
        if mt == PLAIN_TEXT_MSG:
            LENGTH = PLAIN_TEXT_MSG_LENGTH 
        
        if mt == UNICODE_MSG:
            LENGTH = UNICODE_MSG_LENGTH
        
        if mt not in [PLAIN_TEXT_MSG, UNICODE_MSG]:
            error = "Invalid Message Type"
        
        msg_length = len(msg)
        msg_qty = math.ceil(msg_length/LENGTH)
        quantity = mno_count * msg_qty # The total number of SMS credit to be used.

        return quantity, msg_qty, msg, error 

    def send_sms(self, mno, msg, mt, public_id, user, sid=None):
        """
        Formats mno, msg and determines the total number of sms credit to use. Then, deducts the sms credit from 
        the sms account and finally stores the sms to ShortMessage Model where Smsprovider will take over.

        :param mno: Mobile Number, can be seperated by commas if many.
        :param msg: The message to be sent. 
        :param mt: Message Type, 0=English, 1=Arabic or any other language.
        :param public_id: The public_id of the SMS account to be used in sending the SMS.
        :param user: A User model instance. Most be the owner of the sms account.
        :param sid: Sender Id, defaults to SMSAccount.name if not provided.

        Returns a dictionary. Always check for, 
            if res['success'] is True:
                ...it was successful.
        """

        account = SMSAccount.get_account_using_public_id(public_id)
        if account is None:
            return {"success": False, "message": "Invalid Message Account Public Id"}
        
        if account.owner_id != user.id:
            return {"success": False, "message": "Permission Denied, Does not own SMS Account."}
        
        mno_count, mno_list , error = self._format_mno(mno)
        
        if error:
            return {"success": False, "message": error}

        quantity, msg_qty, msg, error = self._format_msg(msg, mno_count, mt)

        if error:
            return {"success": False, "message": error}
        
        if account.balance < quantity:
            return {"success": False, "message": "Insufficient SMS credit."}
        
        batch_id = ShortMessage.generate_batch_id()
        description = f"SMS sent batch {batch_id}"
        res = self.transfer(account.public_id, config.SENT_SMS_ACCOUNT, quantity, account.owner_id, description)
        
        if res['success'] is False:
            return {"success": False, "message": res['message']}

        if sid is None:
            sid = account.name 
        
        sms_list = []
        for num in mno_list:
            sms = ShortMessage(
                batch_id=batch_id, account_id=account.id, user_id=user.id, mno=num, sid=sid, msg=msg, quantity=msg_qty, 
                status=sms_status.submitted, mt=mt 
            )
            sms.set_reference()
            sms_list.append(sms)
        db.session.bulk_save_objects(sms_list)
        db.session.commit()

        msgs = ShortMessage.get_messages_using_batch_id(batch_id)
        return {"success": True, "sms_list": msgs, "quantity": quantity}

sms_manager = Manager()
