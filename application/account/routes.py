from flask import request, g, jsonify

from application import app, db
from application.models.account import User 
from application.models.smscenter import SMSAccount
from application.account.lib.gloxon import gloxonAuth
from application.utils.auth import generate_token


@app.route('/', methods=['GET'])
def home():
    return jsonify({}), 200


@app.route('/account/v1/token', methods=['POST'])
def get_token():
    data = request.get_json()
    authorization_code = data.get('authorization_code')
    referrer_id = data.get('rid', None)

    res = gloxonAuth.exchangeAuthorizationCode(authorization_code)
    if res['success']:
        gx_user = res['user']  # gloxon_user
        public_id = gx_user.get('public_id')
        email = gx_user.get('email')
        token = res.get('token').get('token')
        refresh = res.get('token').get('refresh')

        # Create user account if it does not exist.
        created = False 
        user = User.get_user_using_public_id(public_id)
        if user is None:
            user = User(public_id=public_id, email=email)
            created = True

            if referrer_id:
                referrer = User.get_user_using_public_id(referrer_id)
                if referrer is not None:
                    user.referrer_id = referrer.id  
        user.gloxon_token = token 
        user.gloxon_refresh = refresh 
        db.session.add(user)
        db.session.commit()

        if created: # Create an SMS default account.
            name = gx_user.get('first_name')[:11]
            account = SMSAccount(owner_id=user.id, name=name, is_default=True)
            account.is_floataccount=False
            account.set_public_id()
            db.session.add(account)
            db.session.commit()
            
        # request for a user token.
        token = generate_token(user)
        user_info = res.get('user')

        # Add some valuable information to the existing user info.
        user_info['is_affiliate'] = user.is_affiliate
        user_info['is_admin'] = user.is_admin 
        response = jsonify({"success": True, "token": token, "user": user_info}), 200
    else:
        response = jsonify({"success": False, "token": "", "message": "Invalid Authorization Code"}), 404

    return response 
