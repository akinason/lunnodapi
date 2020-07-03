import requests
import urllib

URL = 'http://gloxonsms.com:9800'


class GloxonSMS:

    def __init__(self, username, password):
        self.base_url = URL
        self.username = username
        self.password = password 

    def send_sms(self, mno, msg, sid, mt=0, fl=0):
        url = f"{self.base_url}/bulksms"
        params = {
            "mno": mno, "msg": msg, "sid": sid, "mt": mt, "fl": fl, "password": self.password, "username": self.username
        }
        message_id = ''
        err = ""
        success = True 
        
        encoded_params = urllib.parse.urlencode(params)
        try:
            response = requests.get(url=url, params=encoded_params)
            status_code = response.status_code
            try:
                message_id = response.content.decode('ascii')
                message_id = message_id[4:]
            except AttributeError:
                message_id = response.content
                message_id = message_id[4:]
            except Exception:
                message_id = response.content
                message_id = message_id[4:]
        except Exception as err:
            status_code = 404
            success = False

        res = {'status_code': int(status_code), 'message_id': message_id, 'error': err, "success": success}
        return res 
                
    
