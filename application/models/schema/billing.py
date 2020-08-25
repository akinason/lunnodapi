from marshmallow import fields, ValidationError, post_dump, post_load, validate

from application import ma
from application.models.account import User
from application.models.smscenter import SMSAccount 
from application.models.billing import PriceList, PaymentGateway


class PaymentGatewaySchema(ma.Schema):
    id = fields.Integer(required=False)

    name = fields.String(required=True)
    payment_url = fields.String(required=True)
    active = fields.Boolean(default=False)

    alt_name = fields.String(required=False)
    description = fields.String(required=False)
    website = fields.String(required=False)
    logo = fields.String(required=False)
    callback_url = fields.String(required=False)
    params = fields.Dict(required=False)

    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)


class PaymentGatewayUpdateSchema(ma.Schema):
    id = fields.Integer(required=True)

    name = fields.String(required=False)
    payment_url = fields.String(required=False)
    active = fields.Boolean(default=False)

    alt_name = fields.String(required=False)
    description = fields.String(required=False)
    website = fields.String(required=False)
    logo = fields.String(required=False)
    callback_url = fields.String(required=False)
    params = fields.Dict(required=False)

    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)


class PriceListBase(ma.Schema):
    account_pid = None
    user_pid = None
    is_standard = None 
    account = None 
    user = None 
    pl = None 

    id = fields.Integer(required=False)

    min_quantity = fields.Integer(required=True)
    max_quantity = fields.Integer(required=True)
    price = fields.Number(required=True)
    currency = fields.String(required=True, validate=validate.Length(max=3), default='USD')

    name = fields.String(required=False, validate=validate.Length(max=50))
    user = fields.Integer(required=False)
    smsaccount = fields.Integer(required=False)
    is_standard = fields.Boolean(default=False)
    active = fields.Boolean(dump_only=True)

    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)

    def post_load_operations(self, data, many, **kwargs):
        self.account_pid = data.get('smsaccount')
        self.user_pid = data.get('user')
        self.is_standard = data.get('is_standard')


        if self.user_pid:
            self.user = User.get_user_using_public_id(data.get('user'))
            if self.user is None:
                raise ValidationError({"user": "Invalid user."})
            data['user_id'] = self.user.id 
            data.pop('user')

        if self.account_pid:
            self.account = SMSAccount.get_account_using_public_id(data.get('smsaccount'))
            if self.account is None:
                raise ValidationError({"smsaccount": "Invalid SMS Account."})
            data['smsaccount_id'] = self.account.id
            data.pop('smsaccount')
          
        
        if (self.account_pid and self.user_pid) and self.account.owner != self.user:
            raise ValidationError({"user": "The SMS Account does not belong to this user."})
        
        if self.is_standard and (self.account_pid or self.user_pid):
            raise ValidationError({"is_standard": 'A standard price list cannot be assigned to a user or an SMS Account.'})
        
        return data 

    def _map_userid_and_smsaccountid_to_public_ids(self, user_id=None, smsaccount=None):
        if user_id:
            user = User.get_user_using_id(user_id)
            return int(user.public_id) if user else ""
        
        if smsaccount:
            account = SMSAccount.get_account_using_id(smsaccount)
            return account.public_id if account else ""

    def post_dump_operations(self, data, many, **kwargs):
       
        return data 


class PriceListSchema(PriceListBase):
    id = fields.Integer(required=False)

    min_quantity = fields.Integer(required=True)
    max_quantity = fields.Integer(required=True)
    price = fields.Number(required=True)
    currency = fields.String(required=True, validate=validate.Length(max=3), default='USD')

    @post_load(pass_many=False)
    def post_load_operations(self, data, many, **kwargs):
        data = super().post_load_operations(data, many, **kwargs)
        if not self.is_standard and not self.account_pid and not self.user_pid:
            raise ValidationError({"is_standard": "You must either mark this as standard or assign it to a user or SMS account."})
        return data 

    @post_dump(pass_many=True)
    def post_dump_operations(self, data, many, **kwargs):
        data = super().post_dump_operations(data, many, **kwargs)
        return data 


class PriceListUpdateSchema(PriceListBase):
    id = fields.Integer(required=True)

    min_quantity = fields.Integer(required=False)
    max_quantity = fields.Integer(required=False)
    price = fields.Number(required=False)
    currency = fields.String(required=False, validate=validate.Length(max=3), default='USD')
   

    @post_load(pass_many=False)
    def post_load_operations(self, data, many, **kwargs):
        data = super().post_load_operations(data, many, **kwargs)
        self.pl = PriceList.get_pricelist_using_id(data.get('id'))

        if self.pl is None:
            raise ValidationError({"id": "Invalid Price List ID."})
        
        if self.is_standard and (self.pl.owner or self.pl.smsaccount):
            raise ValidationError({"is_standard": "You Cannot convert a user price list to a standard price list."})

        if (self.user_pid or self.account_pid) and self.pl.is_standard:
            raise ValidationError({"is_standard": "You cannot convert a standard price list to a personal price list."})
        
        if (self.pl.smsaccount and self.user_pid) and int(self.pl.smsaccount.owner.public_id) != self.user_pid:
            raise ValidationError({"user": "This pricelist belongs to a different user."})

        if (self.pl.user and self.account_pid) and  (self.pl.user.id != self.account.owner.id):
            raise ValidationError({"smsaccount": "This pricelist belongs to a different user."})

        return data 

    @post_dump(pass_many=True)
    def post_dump_operations(self, data, many, **kwargs):
        data = super().post_dump_operations(data, many, **kwargs)
        return data 


class TransactionSchema(ma.Schema):
    id = fields.Integer(dump_only=True)

    amount = fields.Number(required=True)
    currency = fields.String(required=True)
    quantity = fields.Integer(required=True)
    pricelist_id = fields.Integer(required=True)
    smsaccount = fields.Integer(required=False)
    payment_gateway_id = fields.Integer(required=False)

    description = fields.String(required=False)

    transaction_type = fields.String(dump_only=True)
    is_paid = fields.Boolean(dump_only=True)
    is_verified = fields.Boolean(dump_only=True)
    is_complete = fields.Boolean(dump_only=True)
    reference = fields.String(dump_only=True)
    external_reference = fields.String(dump_only=True)
    created = fields.DateTime(dump_only=True)
    updated = fields.DateTime(dump_only=True)


class TransactionUpdateSchema(ma.Schema):
    id = fields.Integer(required=False)
    payment_gateway_id = fields.Integer(required=True)
    response_data = fields.Dict(required=True)
    is_paid = fields.Boolean(required=True)

    @post_load
    def post_load_operations(self, data, many, **kwargs):
        pg_id = data.get('payment_gateway_id')
        pg = PaymentGateway.get_payment_gateway_using_id(pg_id)
        if pg is None:
            raise ValidationError({"payment_gateway_id": "The payment gateway with id %s does not exist." % pg_id})

        return data 
    