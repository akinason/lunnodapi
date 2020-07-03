from flask import jsonify 

from application import db 
from application.models.smscenter import SMSAccount, ShortMessage
from application.models.schema.smscenter import SMSAccountSchema, ShortMessageSchema
from application.smscenter.manager import sms_manager 


class SMSController:

    def __init__(self):
        pass 

    def transfer_sms_credit(self, source, dest, quantity, user):

        source_account = SMSAccount.get_account_using_public_id(source)
        dest_account = SMSAccount.get_account_using_public_id(dest)

        if quantity <= 0:
            return jsonify({"success": False, "message": "Invalid quantity. Operation Not allowed"}), 402

        if source_account is None:
            return jsonify({"success": False, "message": "Invalid Destination Account. Operation Not allowed"}), 402

        if dest_account is None:
            return jsonify({"success": False, "message": "Invalid Source Account. Operation Not allowed"}), 402
        
        if source_account.owner_id != user.id:
            return jsonify({"success": False, "message": "Operation Not allowed. You do not own the source account."}), 402

        if not source_account.is_floataccount and dest_account.owner_id != source_account.owner_id:
            # If it's not an inter account transfer, and the source account is not a FLOAT account, stop it.
            return jsonify({"success": False, "message": "You cannot transfer to another person from a non float account."}), 402

        res = sms_manager.transfer(source, dest, quantity, user.id)
        if res['success']:
            return jsonify({"success": True, "message": "Operation successful."}), 200
        else:
            return jsonify({"success": False, "message": res['message']})

    def get_accounts(self, user):
        accounts = SMSAccount.get_all_user_accounts(user.id)
        _accounts = SMSAccountSchema().dump(accounts, many=True) 
        return jsonify({"success": True, "data": _accounts}), 200

    def get_single_account(self, public_id, user):
        account = SMSAccount.get_account_using_public_id(public_id)
        if account is None or account.owner_id != user.id:
            return jsonify({"success": False, "message": "Account Not Found"}), 404

        return jsonify({"success": True, "data": SMSAccountSchema().dump(account)}), 200

    def create_sms_account(self, name, user):
        account = SMSAccount(name=name, is_default=False, owner_id=user.id, is_floataccount=False)
        account.set_public_id()
        db.session.add(account)
        db.session.commit()
        return jsonify({"success": True, "data": SMSAccountSchema().dump(account)}), 200

    def send_sms(self, mno, msg, mt, public_id, user, sid=None):
        res = sms_manager.send_sms(mno, msg, mt, public_id, user, sid)
        if not res['success']:
            return jsonify({"success": False, "message": res['message']}), 402
        
        return jsonify({
            "success": True, "data": ShortMessageSchema().dump(res['sms_list'], many=True), "quantity": res['quantity']
        }), 200

    def get_single_sms(self, reference, user):
        sms = ShortMessage.get_message_using_reference(reference)

        if sms is None:
            return jsonify({"success": False, "message": "Invalid reference"}), 404

        if sms.user_id != user.id:
            return jsonify({"success": False, "message": "Invalid reference"}), 404
        
        return jsonify({"success": True, "data": ShortMessageSchema().dump(sms)}), 200

    def get_batch_sms(self, batch_id, user):
        smss = ShortMessage.get_messages_using_batch_id_and_user_id(batch_id, user.id)
 
        if smss is None:
            return jsonify({"success": False, "message": "Invalid batch id"}), 404
        
        return jsonify({"success": True, "data": ShortMessageSchema().dump(smss, many=True)}), 200

    def get_sms_log(self, user, public_id=None, page=1, limit=1000):
        """ 
        Returns the list of SMS sent by a given user account.
        """
        smss = ShortMessage.query.filter_by(user_id=user.id)
        if public_id:
            smss = smss.filter_by(account_id=public_id)
        
        smss = smss.paginate(page=page, per_page=limit, max_per_page=1000, error_out=False)

        prev_num = 0 if smss.prev_num is None else 0
        return jsonify({
            "success": True, "data": ShortMessageSchema().dump(smss.items, many=True), "next": smss.next_num, "prev": prev_num,
            "total": smss.total, "pages": smss.pages
        }), 200 
 

sms_controller = SMSController()