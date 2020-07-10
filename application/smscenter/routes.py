from flask import request, g, jsonify

from application import app 
from application.models.account import User 
from application.models.smscenter import SMSAccount
from application.smscenter.controller import sms_controller
from application.utils.auth import requires_auth 


@app.route('/sms/v1/transfer', methods=['POST'])
@requires_auth 
def transfer_sms_credit():
    data = request.get_json()
    source = int(data.get('source'))
    dest = int(data.get('dest'))
    quantity = int(data.get('quantity'))
    user = User.get_user_using_public_id(g.user.get('id'))
    return sms_controller.transfer_sms_credit(source, dest, quantity, user)


@app.route('/sms/v1/accounts', methods=['GET'])
@requires_auth 
def check_accounts():
    id = g.user.get('id')
    user = User.get_user_using_public_id(id)
    return sms_controller.get_accounts(user)


@app.route('/sms/v1/accounts/<int:public_id>', methods=['GET'])
@requires_auth
def check_single_account(public_id):
    id = g.user.get('id')
    user = User.get_user_using_public_id(id)
    return sms_controller.get_single_account(public_id, user)


@app.route('/sms/v1/accounts/<int:public_id>/info', methods=['GET'])
@requires_auth
def get_account_info(public_id):
    return sms_controller.get_account_info(public_id)


@app.route('/sms/v1/accounts/create', methods=['POST'])
@requires_auth
def create_sms_account():
    name = request.get_json().get('name')
    callback_url = request.get_json().get('callback_url', None)
    id = g.user.get('id')
    user = User.get_user_using_public_id(id)
    return sms_controller.create_sms_account(name, user, callback_url)


@app.route('/sms/v1/accounts/update', methods=['POST'])
@requires_auth
def update_sms_account():
    data = request.get_json()
    public_id = data.get('public_id', None)
    name = data.get('name', None)
    callback_url = data.get('callback_url', None)
    user = User.get_user_using_public_id(g.user.get('id'))
    return sms_controller.update_sms_account(public_id, user, name, callback_url)


@app.route('/sms/v1/sendsms', methods=['POST'])
@requires_auth
def send_sms():
    data = request.get_json()
    user = User.get_user_using_public_id(g.user.get('id'))
    mno = data.get('mno')
    msg = data.get('msg')
    mt = int(data.get('mt', 0))
    public_id = data.get('account')
    sid = data.get('sid', None)
    return sms_controller.send_sms(mno, msg, mt, public_id, user, sid)


@app.route('/sms/v1/sms/<string:reference>', methods=['GET'])
@requires_auth
def get_single_sms(reference):
    user = User.get_user_using_public_id(g.user.get('id'))
    return sms_controller.get_single_sms(reference, user)


@app.route('/sms/v1/sms/batch/<string:batch_id>', methods=['GET'])
@requires_auth
def get_batch_sms(batch_id):
    user = User.get_user_using_public_id(g.user.get('id'))
    return sms_controller.get_batch_sms(batch_id, user)


@app.route('/sms/v1/sms/log', methods=['GET'])
@requires_auth
def get_sms_log():
    public_id = request.args.get('public_id', None) 
    page = int(request.args.get('page', 1)) 
    limit = int(request.args.get('limit', 1000))
    user = User.get_user_using_public_id(g.user.get('id'))
    return sms_controller.get_sms_log(user, public_id, page, limit)
