import requests
import urllib
import threading
import time 
import random 

from application.smsprovider.lib.base import SMSStatus, AuthRequiredException


URL = 'http://gloxonsms.com:9800'
sms_status = SMSStatus()


class GloxonSMS:

    def __init__(self, username=None, password=None, session=None):
        self.base_url = URL
        self.username = username
        self.password = password 
        self.threadLocal = threading.local()
        self.failed = "failed"
        self.delivrd = "DELIVRD"
        self.undeliv = "UNDELIV"
        self.expired = "expired"
        self.rejected = "rejected"

        if session:
            self._set_session(session)
    
    def _get_session(self, value=None):
        if not hasattr(self.threadLocal, "session"):
            self.threadLocal.session = requests.Session()
        return self.threadLocal.session 

    def _set_session(self, session):
        if not hasattr(self.threadLocal, "session"):
            self.threadLocal.session = session
    
    def _status_mapper(self, gloxon_status):
        """
        Returns the corresponding Lunnod status based on the given gloxon_status.
        """ 
        if gloxon_status.lower() == self.failed.lower():
            return sms_status.failed
        elif gloxon_status.lower() == self.delivrd.lower():
            return sms_status.delivered
        elif gloxon_status.lower() == self.undeliv.lower():
            return sms_status.undelivered
        elif gloxon_status.lower() == self.expired.lower():
            return sms_status.expired
        elif gloxon_status.lower() == self.rejected.lower():
            return sms_status.rejected
        else:
            return sms_status.general

    def send_sms(self, mno, msg, sid, mt=0, fl=0):
        if not self.username or not self.password:
            raise AuthRequiredException("Username and Password Required.")

        session = self._get_session()

        url = f"{self.base_url}/bulksms"
        params = {
            "mno": mno, "msg": msg, "sid": sid, "mt": mt, "fl": fl, "password": self.password, "username": self.username
        }
        message_id = ''
        err = ""
        success = True 
        duration = 0
        start_time = time.time()

        encoded_params = urllib.parse.urlencode(params)
        try:
            response = session.get(url=url, params=encoded_params)
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
        duration = time.time() - start_time

        res = {'status_code': int(status_code), 'message_id': message_id, 'error': err, "success": success, "response_time": duration}
        return res 
    
    def simulator(self, mno, msg, sid, mt=0, fl=0):
        """
        Simulates the send sms function above. A real HTTP command is not sent.
        """
       
        # rand = random.randint(1, 1)
        rand = 1
        time.sleep(rand)

        if random.random() >= 0.5:
            success = True 
            message_id = random.randint(100, 5000000)
            status_code = 200
            err = ""
        else:
            success = False 
            message_id = ""
            status_code = 400
            err = "Operation not successful"

        res = {'status_code': int(status_code), 'message_id': message_id, 'error': err, "success": success, "response_time": rand}
        return res 

    def format_callback(self, mno, sid, msgid, date, status):
        response = {"mno": mno, "sid": sid, "msgid": msgid, "date": date, "status": status}
        message_id = msgid
        _status = self._status_mapper(status)
        return {"message_id": message_id, "status": _status, "response": response}

    
    
if __name__ == "__main__":
    import time 

    s = time.time()
    gloxon = GloxonSMS("gloxon", "panama245@")
    r = gloxon.simulator("237655916762", "This is a basic test.", "Empire")
    e = time.time()
    print(r)
    print('Request took ', e - s, "seconds")
   

