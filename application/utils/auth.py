import random

from functools import wraps

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


def requires_auth(f):
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
