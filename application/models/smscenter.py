from datetime import datetime 

from sqlalchemy import or_

from application import db 
from application.utils.auth import generate_random_numbers 

class SMSStatus:
    def __init__(self):
        self.submitted = 'SUBMITTED'
        self.sent = 'SENT'
        self.delivered = 'DELIVERED'
        self.failed = 'FAILED'


sms_status = SMSStatus()


class SMSAccount(db.Model):
    __tablename__ = 'smsaccounts'

    id = db.Column(db.Integer(), primary_key=True)
    public_id = db.Column(db.Integer(), index=True)
    name = db.Column(db.String(11), nullable=True)
    owner_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    owner = db.relationship('User', backref='smsaccount', lazy=True)
    is_default = db.Column(db.Boolean(), default=True)
    is_floataccount = db.Column(db.Boolean(), default=True)
    balance = db.Column(db.Integer(), default=0)
    total_sent = db.Column(db.Integer(), default=0)
    historic_total = db.Column(db.Integer(), default=0)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow())
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow(), onupdate=datetime.utcnow())

    def set_public_id(self):
        if not self.public_id:
            id = generate_random_numbers(7)
            while SMSAccount.get_account_using_public_id(id):
                id = generate_random_numbers(7)
            self.public_id = id 

    def __int__(self):
        return self.public_id

    @staticmethod
    def get_account_using_public_id(public_id):
        account = SMSAccount.query.filter_by(public_id=public_id).first()
        return account if account else None 
    
    @staticmethod
    def get_account_using_id(id):
        account = SMSAccount.query.filter_by(id=id).first()
        return account if account else None 
    
    @staticmethod
    def get_all_user_accounts(user_id):
        accounts = SMSAccount.query.filter_by(owner_id=user_id).all()
        return accounts

    @staticmethod 
    def get_all_user_account_public_ids(user_id):
        accounts = SMSAccount.query.filter_by(owner_id=user_id).all()
        if accounts:
            return [a.public_id for a in accounts]
        return []

    @staticmethod
    def get_default_user_sms_account(user_id):
        account = SMSAccount.query.filter_by(owner_id=user_id, is_default=True).first()
        return account if account else None 

class ShortMessage(db.Model):
    __tablename__ = 'shortmessages'

    id = db.Column(db.Integer(), primary_key=True)
    batch_id = db.Column(db.Integer())
    reference = db.Column(db.String(50))
    account_id = db.Column(db.Integer(), db.ForeignKey('smsaccounts.id'))
    account = db.relationship('SMSAccount', backref='messages', lazy=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    user = db.relationship('User', backref='messages', lazy=True)
    mno = db.Column(db.String(30))
    sid = db.Column(db.String(11))
    mt = db.Column(db.Integer())
    msg = db.Column(db.String(1000))
    quantity = db.Column(db.Integer(), default=1)
    status = db.Column(db.String(30), default=sms_status.submitted)
    response = db.Column(db.String(1000), nullable=True)
    provider_id = db.Column(db.Integer(), nullable=True)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow())
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow(), onupdate=datetime.utcnow())

    def set_reference(self):
        if not self.reference:
            ref = str(generate_random_numbers(10))
            while ShortMessage.get_message_using_reference(ref):
                ref = str(generate_random_numbers(10))
            self.reference = ref
    
    @staticmethod
    def generate_batch_id():
        id = generate_random_numbers(8)
        while ShortMessage.get_messages_using_batch_id(id):
            id = generate_random_numbers(8)
        return id 
    
    @staticmethod
    def get_message_using_id(id):
        msg = ShortMessage.query.filter_by(id=id).first()
        return msg if msg else None 
    
    @staticmethod
    def get_message_using_reference(reference):
        msg = ShortMessage.query.filter_by(reference=str(reference)).first()
        return msg if msg else None 
    
    @staticmethod
    def get_messages_using_batch_id(batch_id):
        msgs = ShortMessage.query.filter_by(batch_id=batch_id).all()
        return msgs if msgs else None 

    @staticmethod
    def get_messages_using_batch_id_and_user_id(batch_id, user_id):
        msgs = ShortMessage.query.filter_by(batch_id=batch_id, user_id=user_id).all()
        return msgs if msgs else None 

class SMSTransaction(db.Model):
    __tablename__ = 'sms_transactions'

    id = db.Column(db.Integer(), primary_key=True)
    source_account_id = db.Column(db.Integer(), db.ForeignKey('smsaccounts.id'))
    dest_account_id = db.Column(db.Integer(), db.ForeignKey('smsaccounts.id'))
    quantity = db.Column(db.Integer())
    reference = db.Column(db.String(50))
    description = db.Column(db.String(150), nullable=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    source_balance = db.Column(db.Integer(), default=0)
    dest_balance = db.Column(db.Integer(), default=0)
    user = db.relationship('User', backref='sms_transactions', lazy=True)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow())
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow(), onupdate=datetime.utcnow())

    def set_reference(self):
        if not self.reference:
            ref = str(generate_random_numbers(8))
            while ShortMessage.get_message_using_reference(ref):
                ref = str(generate_random_numbers(8))
            self.reference = ref 
    
    @staticmethod
    def get_transaction_using_reference(reference):
        transaction = SMSTransaction.query.filter_by(reference=reference).first()
        return transaction if transaction else None 
    
    @staticmethod
    def get_user_transactions(user_id):
        """
        Returns all transactions performed by a certain user_id
        """
        txns = SMSTransaction.query.filter_by(user_id=user_id).all()
        return txns 
    
    @staticmethod
    def get_account_transactions(account_id):
        """
        Returns all transactions affecting an smsaccount. Be it, source or destination
        """ 
        txns = SMSTransaction.query.filter(
            or_(SMSTransaction.source_account_id == account_id,  SMSTransaction.dest_account_id == account_id)
        ).all()
        return txns 

    @staticmethod
    def get_user_accounts_transactions(user_id):
        """
        Returns all transactions affecting smsaccounts belonging to the given user_id. Be it source or destination.
        """
        sms_accounts = SMSAccount.get_all_user_accounts(user_id)
        accounts = [a.id for a in sms_accounts]
        txns = SMSTransaction.query.filter(
            or_(SMSTransaction.source_account_id.in_(accounts),  SMSTransaction.dest_account_id.in_(accounts))
        ).all()

        return txns

     
    