from flask import request, jsonify, g, render_template

from marshmallow import ValidationError

from application import app, db, gm_client
from application.utils.auth import requires_auth, requires_app_auth
from application.models.schema.billing import (
        TransactionSchema, PriceListSchema, PaymentGatewaySchema, PaymentGatewayUpdateSchema, PriceListUpdateSchema,
        TransactionUpdateSchema
    )
from application.models.smscenter import SMSAccount
from application.models.billing import  BillingTransaction, PriceList, PaymentGateway
from application.models.account import User 
from application.billing.manager import Manager


@app.route('/billing/pricelists', methods=['POST'])
@requires_app_auth
def create_billing_pricelist():
    if not request.json:
        return jsonify({"success": False, "message": {"general": "json data required."}}), 400

    try:
        data = PriceListSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({"success": False, "message": e.messages}), 400
    if 'id' in data.keys(): data.pop('id')

    pl = PriceList(**data)
    db.session.add(pl)
    db.session.commit()
    return jsonify({"success": True, "data": PriceListSchema().dump(pl)}), 200


@app.route('/billing/pricelists', methods=['PUT'])
@requires_app_auth
def update_billing_pricelist():
    if not request.json:
        return jsonify({"success": False, "message": {"json_data": "json data required."}}), 400

    try:
        data = PriceListUpdateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({"success": False, "message": e.messages}), 400

    if not 'id' in data.keys():
        return jsonify({"success": False, "message": {"id": "id is required to update the pricelist."}}), 400

    pl = PriceList.get_pricelist_using_id(data.get('id'))
    if pl is None:
        return jsonify({"success": False, "message": {"id": "id is required to update the pricelist."}}), 400

    data.pop('id')
    db.session.query(PriceList).filter(PriceList.id == pl.id).update(data)
    db.session.commit()
    return jsonify({"success": True, "data": PriceListUpdateSchema().dump(pl)}), 200


@app.route('/billing/pricelists', methods=['GET'])
@requires_app_auth
@requires_auth
def get_billing_pricelists():
    id = request.args.get('id', None)
    user_public_id = request.args.get('user', None)

    if id:
        pl = PriceList.get_pricelist_using_id(id)
        if pl is None:
            return jsonify({"success": False, "message": {"id": "Invalid Pricelist Id."}}), 404
        return jsonify({"success": True, "data": PriceListSchema().dump(pl)}), 200

    if user_public_id:
        if user_public_id != g.user.get('id'): return jsonify({"success": False, "message": {"user": "Invalid User Public Id. Must be public id of current user."}}), 404
        user = User.get_user_using_public_id(user_public_id)
        pls = PriceList.get_user_pricelists(user.id)
        return jsonify({"success": True, "data": {"custom": PriceListSchema().dump(pls)}}), 200

    user = User.get_user_using_public_id(g.user.get('id'))
    standard_pricelists = PriceList.get_standard_sms_pricelists()
    custom_pricelists = PriceList.get_user_pricelists(user.id)

    return jsonify({
        "success": True,
        "data": {"standard": PriceListSchema().dump(standard_pricelists, many=True), "custom": PriceListSchema().dump(custom_pricelists, many=True)},
    }), 200 


@app.route('/billing/pricelists/standard', methods=['GET'])
@requires_app_auth
def get_standard_billing_pricelists():
    id = request.args.get('id', None)

    if id:
        pl = PriceList.get_pricelist_using_id(id)
        if pl is None or not pl.is_standard:
            return jsonify({"success": False, "message": {"id": "Invalid Pricelist Id."}}), 404
        return jsonify({"success": True, "data": PriceListSchema().dump(pl)}), 200
    
    standard_pricelists = PriceList.get_standard_sms_pricelists()

    return jsonify({
        "success": True,
        "data": {"standard": PriceListSchema().dump(standard_pricelists, many=True)},
    }), 200 


@app.route('/billing/paymentgateways', methods=['POST'])
@requires_app_auth
def create_paymentgateway():
    if not request.json:
        return jsonify({"success": False, "message": {"json_data": "json data required."}}), 400

    try:
        data = PaymentGatewaySchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({"success": False, "message": e.messages}), 400

    if 'id' in data.keys(): data.pop('id')

    pg = PaymentGateway(**data)
    if 'params' in data.keys():
        pg.encrypt_params()
    db.session.add(pg)
    db.session.commit()
    pg.decrypt_params()
    return jsonify({"success": True, "data": PaymentGatewaySchema().dump(pg)}), 200


@app.route('/billing/paymentgateways', methods=['PUT'])
@requires_app_auth
def update_paymentgateway():
    if not request.json:
        return jsonify({"success": False, "message": {"json_data": "json data required."}}), 400

    try:
        data = PaymentGatewayUpdateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({"success": False, "message": e.messages}), 400

    if not 'id' in data.keys(): return jsonify({"success": False, "message": {"id": "Id required to perform an update."}}), 400

    pg = PaymentGateway.get_payment_gateway_using_id(data.get('id'))
    if pg is None: return jsonify({"success": False, "message": {"id": "Payment Gateway not found."}}), 404

    id = data.pop('id')
    db.session.query(PaymentGateway.id).filter(PaymentGateway.id == id).update(data)
    db.session.add(pg)
    db.session.commit()

    if 'params' in data.keys():
        pg.encrypt_params()
        db.session.add(pg)
        db.session.commit()
    pg.decrypt_params()  
    return jsonify({"success": True, "data": PaymentGatewayUpdateSchema().dump(pg)}), 200


@app.route('/billing/paymentgateways', methods=['GET'])
@requires_app_auth
def get_paymentgateway():
    id = request.args.get('id', None)

    if id:
        pg = PaymentGateway.get_payment_gateway_using_id(id)
        if pg is None: return jsonify({"success": False, "message": {"id": "Payment Gateway not found."}}), 404
        return jsonify({"success": True, "data": PaymentGatewaySchema().dump(pg)}), 200

    pgs = PaymentGateway.get_all_active_payment_gateways()
    _pgs = []
    for pg in pgs:
        pg.decrypt_params()
        _pgs.append(pg)
    return jsonify({"success": True, "data": PaymentGatewaySchema().dump(_pgs, many=True)}), 200


@app.route('/billing/transactions', methods=['POST'])
@requires_app_auth
@requires_auth
def billing_transaction():
    """
    Route used when a customer request to do payment for a particular package.
    """
    if not request.json:
        return jsonify({"success": False, "message": {"json_data": "json data required."}}), 400

    try:
        data = TransactionSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({"success": False, "message": e.messages}), 400
    
    user = User.get_user_using_public_id(g.user.get('id'))
    data['user_id'] = user.id 
    if not "smsaccount" in data.keys():
        data["smsaccount_id"] = SMSAccount.get_default_user_sms_account(user.id).id 
    data['transaction_type'] = BillingTransaction.SMS_SALES

    txn = BillingTransaction(**data)

    db.session.add(txn)
    db.session.commit()

    pgs = PaymentGateway.get_all_active_payment_gateways()
    _pgs = []
    for pg in pgs:
        pg.decrypt_params()
        _pgs.append(pg)

    return jsonify({"success": True, "data": {"transaction": TransactionSchema().dump(txn), "paymentgateways": PaymentGatewaySchema().dump(_pgs, many=True)}}), 200


@app.route('/billing/transactions', methods=['GET'])
@requires_app_auth
@requires_auth
def get_billing_transactions():
    page = int(request.args.get('page', 1)) 
    limit = int(request.args.get('limit', 1000))
    reference = request.args.get('reference', None)
    id = request.args.get('id', None)

    if id or (id and reference):
        txn = BillingTransaction.get_transaction_using_id(id)
        if txn is None:
            return jsonify({"success": False, "message": {"id": "Invalid Id."}}), 404
        else:
            return jsonify({"success": True, "data": TransactionSchema().dump(txn)}), 200
    
    if reference and not id:
        txn = BillingTransaction.get_transaction_using_reference(reference)
        if txn is None:
            return jsonify({"success": False, "message": {"reference": "Invalid reference."}}), 404
        else:
            return jsonify({"success": True, "data": TransactionSchema().dump(txn)}), 200

    user = User.get_user_using_public_id(g.user.get('id'))
    txns = BillingTransaction.get_user_transactions(user.id, page=page, limit=limit)

    prev_num = 0 if txns.prev_num is None else 0
    return jsonify({
        "success": True, "data": TransactionSchema().dump(txns.items, many=True), "next": txns.next_num, "prev": prev_num,
        "total": txns.total, "pages": txns.pages
    }), 200 


@app.route('/billing/transactions', methods=['PUT'])
@requires_app_auth
@requires_auth
def billing_transaction_update():
    """
    Route used when after payment to update billing transaction.
    """
    if not request.json:
        return jsonify({"success": False, "message": {"json_data": "json data required."}}), 400

    try:
        data = TransactionUpdateSchema().load(request.get_json())
    except ValidationError as e:
        return jsonify({"success": False, "message": e.messages}), 400
    
    txn = BillingTransaction.get_transaction_using_id(data.get('id'))
    if txn is None:
        return jsonify({"success": False, "message": {"general": "Transaction Not Found."}}), 404
    
    if txn.is_complete:
        return jsonify({"success": False, "message": {"general": "Transaction already completed."}}), 400
    
    db.session.query(BillingTransaction).filter(BillingTransaction.id == txn.id).update(**data)
    # txn.response_data = data.get('response_data')
    # txn.is_paid = data.get('is_paid')
    # txn.payment_gateway_id = data.get('payment_gateway_id')
    db.session.commit()
  
    if txn.is_paid:
        gm_client.submit_job("billing.verify_payment", {"transaction_id": txn.id}, background=True, wait_until_complete=False)

    return jsonify({"success": True, "data": {"transaction": TransactionSchema().dump(txn)}}), 200


@app.route('/billing/payment/<string:pg_name>/callback', methods=['POST'])
def payment_gateway_callback_handler(pg_name):
    if not request.json:
        return jsonify({"success": False, "message": {"json_data": "json data required."}}), 400

    pg_name = pg_name.upper()
    data = request.get_json()
    gm_client.submit_job("billing.parse_callback", {"pg_name": pg_name, "data": data}, background=True, wait_until_complete=False)

    return jsonify({"success": True}), 200 

@app.route("/billing/test", methods=["GET", "POST"])
def billing_test():
    return render_template("checkout.html")
    from application.billing.lib.paypal import paypal 
    # paypal._getOrderDetails("2VG64936K0807662Y")
    # paypal._getCapturedPaymentDetails("58V19987BL272640V")

    # return jsonify({}), 200