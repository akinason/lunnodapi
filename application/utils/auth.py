import random

from functools import wraps, partial

from flask import request, g, jsonify
from itsdangerous import SignatureExpired, BadSignature
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from application import app

TWO_WEEKS = 1209600


def generate_token(user, expiration=TWO_WEEKS):
    s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
    token = s.dumps({
        'id': user.public_id,
        'email': user.email,
    })
    _payload, header = s.loads(token, return_header=True)
    return {'token': token.decode('utf-8'), "iat": header['iat'], "exp": header['exp']}


def verify_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except (BadSignature, SignatureExpired):
        return None
    return data


def requires_auth(f=None, *, auth_is_optional=False):
    if f is None:
        return partial(requires_auth, auth_is_optional=auth_is_optional)

    if auth_is_optional:
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
    else:
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', None)
            if token:
                string_token = token.split(" ")[1]
                user = verify_token(string_token)
                if user:
                    g.user = user
                    return f(*args, **kwargs)

            return jsonify(message="Authentication is required to access this resource"), 401

    return decorated


def requires_app_auth(f):
    # Authentication used by Lunnod front end applications.
    # TODO: still to work on the authentication.
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated


def generate_random_numbers(length):
    """
    Generates random numbers for a given length.
    :param length: Length of the generated random number.
    :return: Int: Generated random number.
    """
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    rand = []
    for i in range(length):
        random.shuffle(nums)
        if i != 0:
            rand.append(nums[8 % i])
        else:
            rand.append(nums[i])
    r = ''.join(str(x) for x in rand)
    return int(r)
