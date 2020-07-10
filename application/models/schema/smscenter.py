from marshmallow import fields, post_dump

from application import ma 
from application.models.smscenter import SMSAccount


class SMSAccountSchema(ma.Schema):
    public_id = fields.Integer(dump_only=True)
    name = fields.String()
    is_default = fields.Boolean(dump_only=True)
    is_floataccount = fields.Boolean(dump_only=True)
    balance = fields.Integer(dump_only=True)
    total_sent = fields.Integer(dump_only=True)
    historic_total = fields.Integer(dump_only=True)
    callback_url = fields.String(required=False)
    created_on = fields.DateTime(dump_only=True)
    updated_on = fields.DateTime(dump_only=True)
    owner = fields.String(dump_only=True)


class SMSAccountInfoSchema(ma.Schema):
    public_id = fields.Integer(dump_only=True)
    name = fields.String()
    email = fields.String()

    @post_dump
    def get_email(self, data, many, **kwargs):
        if not many:
            public_id = data.get('public_id')
            account = SMSAccount.get_account_using_public_id(public_id)
            data['email'] = account.owner.email 
        return data  






class ShortMessageSchema(ma.Schema):
    reference = fields.String(dump_only=True)
    batch_id = fields.String(dump_only=True)
    account = fields.Integer()
    mno = fields.String()
    sid = fields.String(default=None)
    mt = fields.Integer(default=0)
    msg = fields.String()
    quantity = fields.Integer(dump_only=True)
    status = fields.String(dump_only=True)
