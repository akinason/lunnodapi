from marshmallow import fields 

from application import ma 


class SMSAccountSchema(ma.Schema):
    public_id = fields.Integer(dump_only=True)
    name = fields.String()
    is_default = fields.Boolean(dump_only=True)
    is_floataccount = fields.Boolean(dump_only=True)
    balance = fields.Integer(dump_only=True)
    total_sent = fields.Integer(dump_only=True)
    historic_total = fields.Integer(dump_only=True)
    created_on = fields.DateTime(dump_only=True)
    updated_on = fields.DateTime(dump_only=True)
    owner = fields.String(dump_only=True)

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