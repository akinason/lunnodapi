import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSON

from application import db
from application.models.account import User  
from application.utils.encryption import cryptograpy


class PaymentGateway(db.Model):
    __tablename__ = 'paymentgateways'

    MONETBIL = "MONETBIL"
    PAYPAL = "PAYPAL"
    FLUTTERWAVE = "FLUTTERWAVE"
    PAYSTACK = "PAYSTACK"
    CINETPAY = "CINETPAY"
    AVAILABLE_INTERNAL_NAMES = [MONETBIL, PAYPAL, FLUTTERWAVE, CINETPAY]


    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    logo = db.Column(db.String(500), nullable=True)
    alt_name = db.Column(db.String(50), nullable=True)  # Alternative name.
    internal_name = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(250), nullable=True)
    website = db.Column(db.String(50), nullable=True)
    payment_url =  db.Column(db.String(250), nullable=True)
    callback_url = db.Column(db.String(250), nullable=True)
    params = db.Column(JSON(), nullable=True, default={})
    active = db.Column(db.Boolean(), default=False)
    created = db.Column(db.DateTime(), default=datetime.utcnow())
    updated = db.Column(db.DateTime(), onupdate=datetime.utcnow(), default=datetime.utcnow())

    def encrypt_params(self):
        # Encrypts payment gateway parameters like username, password, app_key, app_secret, etc. Depending on the payment gateway.
        
        try:
            self.params = {"value": cryptograpy.encrypt(self.params)}
            return True
        except Exception as e:
            print(e)
            return False 

    def decrypt_params(self):
        try:
            self.params = cryptograpy.decrypt(self.params.get('value'))
            return True
        except Exception:
            return False
       

    @staticmethod
    def get_payment_gateway_using_id(id):
        pg = PaymentGateway.query.filter_by(id=id).first()
        return pg if pg else None 

    @staticmethod
    def get_payment_gateway_using_internal_name(internal_name):
        pg = PaymentGateway.query.filter_by(internal_name=internal_name).first()
        return pg if pg else None 
        
    @staticmethod
    def get_all_active_payment_gateways():
        pgs = PaymentGateway.query.filter_by(active=True).all()
        return pgs if pgs else []
    

class PriceList(db.Model):
    __tablename__ = 'pricelists'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    min_quantity = db.Column(db.Integer(), nullable=False)
    max_quantity = db.Column(db.Integer(), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='pricelists', lazy=True)
    active = db.Column(db.Boolean(), default=True)
    smsaccount_id = db.Column(db.Integer(), db.ForeignKey('smsaccounts.id'), nullable=True)
    smsaccount = db.relationship('SMSAccount', backref='pricelists', lazy=True)
    is_standard = db.Column(db.Boolean(), default=False)
    created = db.Column(db.DateTime(), default=datetime.utcnow())
    updated = db.Column(db.DateTime(), onupdate=datetime.utcnow(), default=datetime.utcnow())

    @staticmethod
    def get_pricelist_using_id(id):
        pl = PriceList.query.filter_by(id=id, active=True).first()
        return pl if pl else None 
    
    @staticmethod
    def get_standard_sms_pricelists():
        pls = PriceList.query.filter_by(is_standard=True, active=True).all()
        return pls if pls else []
    
    @staticmethod
    def get_user_pricelists(user_id):
        pls = PriceList.query.filter_by(user_id=user_id, active=True).all()
        return pls if pls else []
    
    @staticmethod
    def get_smsaccount_pricelists(smsaccount_id):
        pls = PriceList.query.filter_by(smsaccount_id=smsaccount_id, active=True).all()
        return pls if pls else []


class BillingTransaction(db.Model):
    __tablename__ = 'billing_transactions'

    SMS_SALES = 'SMS_SALES'
    AFFILIATE_COMMISSION = 'AFFILIATE_COMMISSION'

    id = db.Column(db.Integer(), primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    pricelist_id = db.Column(db.Integer(), db.ForeignKey('pricelists.id'), nullable=True)
    pricelist = db.relationship('PriceList', backref='billing_transactions', lazy=True)
    transaction_type = db.Column(db.String(), nullable=True)
    quantity = db.Column(db.Integer(), nullable=True)
    reference = db.Column(db.String(50), nullable=True, default=uuid.uuid4)
    is_paid = db.Column(db.Boolean(), default=False)
    is_verified = db.Column(db.Boolean(), default=False)
    is_complete = db.Column(db.Boolean(), default=False)
    is_successful = db.Column(db.Boolean(), default=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref='billing_transactions', lazy=True)
    smsaccount_id = db.Column(db.Integer(), db.ForeignKey('smsaccounts.id'), nullable=True)
    smsaccount = db.relationship('SMSAccount', backref='billing_transactions', lazy=True)
    description = db.Column(db.String(250), nullable=True)
    external_reference = db.Column(db.String(250), nullable=True)
    payment_gateway_id = db.Column(db.Integer(), db.ForeignKey('paymentgateways.id'), nullable=True)
    payment_gateway = db.relationship('PaymentGateway', backref='transactions', lazy=True)
    response_data = db.Column(JSON(), nullable=True)
    callback_data = db.Column(JSON(), nullable=True)
    verification_data = db.Column(JSON(), nullable=True)
    created = db.Column(db.DateTime(), default=datetime.utcnow())
    updated = db.Column(db.DateTime(), onupdate=datetime.utcnow(), default=datetime.utcnow())

    @staticmethod
    def get_transaction_using_id(id):
        txn = BillingTransaction.query.filter_by(id=id).first()
        return txn if txn else None 

    @staticmethod
    def get_transaction_using_reference(reference):
        txn = BillingTransaction.query.filter_by(reference=reference).first()
        return txn if txn else None 

    @staticmethod
    def get_user_transactions(user_id, page=1, limit=1000):
        txns = BillingTransaction.query.filter_by(user_id=user_id)
        txns = txns.paginate(page=page, per_page=limit, max_per_page=1000, error_out=False)
        return txns if txns else [] 
    
    @staticmethod
    def get_transactions_by_smsaccount(smsaccount_id, page=1, limit=1000):
        txns = BillingTransaction.query.filter_by(smsaccount_id=smsaccount_id, is_paid=True)
        txns = txns.paginate(page=page, per_page=limit, max_per_page=1000, error_out=False)
        return txns if txns else []
    
    @staticmethod
    def get_transactions_by_pricelist(pricelist_id, page=1, limit=1000):
        txns = BillingTransaction.query.filter_by(pricelist_id=pricelist_id, is_paid=True)
        txns = txns.paginate(page=page, per_page=limit, max_per_page=1000, error_out=False)
        return txns if txns else []
    