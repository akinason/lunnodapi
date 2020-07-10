from flask import request, jsonify

from application import app 
from application.models.smsprovider import *
from application.smsprovider import manager
from application.smsprovider.lib.gloxonsms import GloxonSMS


@app.route('/provider/test', methods=['GET'])
def test_providers():
    manager.send_messages()
    return {}


@app.route('/provider/gloxonsms/callback', methods=['POST'])
def gloxonsms_callback():
    mno = request.args.get('mno')
    sid = request.args.get('sid')
    msgid = request.args.get('msgid')
    date = request.args.get('date')
    status = request.args.get('status')

    gloxon = GloxonSMS()
    formatted = gloxon.format_callback(
        mno=mno, sid=sid, msgid=msgid, date=date, status=status
    )

    manager.handle_callback(
        message_id=formatted.get('message_id'),
        status = formatted.get('status'),
        response = formatted.get('response')
    )

    print('callback received.')
    print(formatted)
    return jsonify({}), 200
