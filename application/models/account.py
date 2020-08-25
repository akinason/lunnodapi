from datetime import datetime

from application import db 
from application.account.lib.gloxon import gloxonAuth


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer(), primary_key=True)
    public_id = db.Column(db.String(50), nullable=True) # Gloxon Public Id
    email = db.Column(db.String(150), nullable=True)
    is_affiliate = db.Column(db.Boolean(), default=False)
    affiliate_docs = db.Column(db.String(255), nullable=True)
    is_admin = db.Column(db.Boolean(), default=False)
    referrer_id = db.Column(db.Integer(), db.ForeignKey('users.id'), index=True)
    referrer = db.relationship(lambda: User, remote_side=id, backref="referrals")
    created_on = db.Column(db.DateTime(), default=datetime.utcnow())
    updated_on = db.Column(db.DateTime(), onupdate=datetime.utcnow())
    gloxon_token = db.Column(db.String(1000), nullable=True)
    gloxon_refresh = db.Column(db.String(1000), nullable=True)
    

    _first_name = ""
    _last_name = ""
    _full_name = ""

    def __str__(self):
        return self.email
    
    def __int__(self):
        return int(self.public_id) 

    @property
    def first_name(self):
        if self._first_name:
            pass 
        else:
            self._set_user_information()
        return self._first_name
    
    @property
    def last_name(self):
        if self._last_name:
            pass 
        else:
            self._set_user_information()
        return self._last_name        

    @property
    def full_name(self):
        if self._full_name:
            pass 
        else:
            self._set_user_information()
        return self._full_name   

    def _set_user_information(self):
        if not self._first_name:
            info = self.get_user_information()
            self._first_name = info.get('first_name')
            self._last_name = info.get('last_name')
            self._full_name = f"{self._first_name} {self._last_name}"

    def get_user_information(self):
        res = gloxonAuth.getUserInformation(self.gloxon_token, self.gloxon_id)
        return res 

    @staticmethod
    def get_user_using_email(email):
        user = User.query.filter_by(email=email).first()
        return user if user else None 
    
    @staticmethod
    def get_user_using_public_id(public_id):
        user = User.query.filter_by(public_id=str(public_id)).first()
        return user if user else None 

    @staticmethod
    def get_user_using_id(id):
        user = User.query.filter_by(id=id).first()
        return user if user else None 

    @staticmethod
    def get_all_affiliates():
        users = User.query.filter_by(is_affiliate=True).all()
        return users 
    