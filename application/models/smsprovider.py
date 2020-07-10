from datetime import datetime 

from application import db  


class Provider(db.Model):
    __tablename__ = 'providers'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), nullable=True, unique=True)
    password = db.Column(db.String(150), nullable=True)
    active = db.Column(db.Boolean(), default=False)
    balance = db.Column(db.Integer(), default=0)
    max_per_second = db.Column(db.Integer(), default=0)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow())
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow(), onupdate=datetime.utcnow())
    is_in_use = db.Column(db.Boolean(), default=False)

    def __str__(self):
        return self.name 

    @staticmethod 
    def get_provider_using_id(id):
        prov = Provider.query.filter_by(id=id, active=True).first()
        return prov if prov else None 

    @staticmethod
    def get_provider_using_username(username):
        prov = Provider.query.filter_by(username=username, active=True).first()
        return prov if prov else None 

    @staticmethod
    def get_providers_not_in_use():
        provs = Provider.query.filter_by(is_in_use=False, active=True).order_by(Provider.balance.desc()).all()
        return provs if provs else None
    
    @staticmethod
    def get_providers_in_use():
        provs = Provider.query.filter_by(is_in_use=True, active=True).order_by(Provider.balance.desc()).all()
        return provs if provs else None
    