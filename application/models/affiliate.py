from datetime import datetime 

from application import db  


class AffiliateInfo(db.Model):
    __tablename__ = 'affiliateinfo'

    id = db.Column(db.Integer, primary_key=True)
    commission_rate = db.Column(db.Numeric(3, 4), default=15.0)
    user_id = db.Column(db.Integer(), db.ForeiegnKey("users.id"), nullable=False, unique=True)
    user = db.relationship('User', backref='affiliate_info')
    outstanding_commission = db.Column(db.Numeric(10, 2), default=0.0)
    available_commission = db.Column(db.Numeric(10, 2), default=0.0)
    total_commission = db.Column(db.Numeric(10, 2), default=0.0)
    created = db.Column(db.DateTime(), default=datetime.utcnow())
    updated = db.Column(db.DateTime(), onupdate=datetime.utcnow(), default=datetime.utcnow())

    @staticmethod
    def get_affiliateinfo_using_user_id(user_id):
        info = AffiliateInfo.query.filter_by(user_id=user_id).first()
        return info if info else None 

    @staticmethod 
    def get_affiliate_info_using_id(id):
        info = AffiliateInfo.query.filter_by(id=id).first()
        return info if info else None 
    

class Commission(db.Model):
    __tablename__ = 'commissions'

    CREATED = 'created'
    PAIDOUT = 'paid_out'
    CANCELLED = 'cancelled'
    ONHOLD = 'on_hold'

    id = db.Column(db.Integer(), primary_key=True)
    affiliate_id = db.Column(db.Integer(), db.ForeiegnKey("users.id"), nullable=False)
    affiliate = db.relationship('User', backref='commissions')
    order_id = db.Column(db.Integer(), db.ForeignKey('billing_transactions.id'), nullable=True)
    order = db.relationship('BillingTransaction', backref='affiliate_commissions')
    sales_amount = db.Column(db.Numeric(10, 2), default=0.0)
    commission_amount = db.Column(db.Numeric(10, 2), default=0.0)
    status = db.Column(db.String(15), default=CREATED)
    is_complete = db.Column(db.Boolean(), default=False)
    created = db.Column(db.DateTime(), default=datetime.utcnow())
    updated = db.Column(db.DateTime(), onupdate=datetime.utcnow(), default=datetime.utcnow())
    