from abc import ABCMeta, abstractmethod
class SMSStatus:
    def __init__(self):
        self.submitted = 'SUBMITTED'
        self.sent = 'SENT'
        self.rejected = 'REJECTED'
        self.delivered = 'DELIVERED'
        self.failed = 'FAILED'
        self.undelivered = 'UNDELIVERED'
        self.expired = 'EXPIRED'
        self.general = 'GENERAL'


class BaseProvider(metaclass=ABCMeta):

    @abstractmethod
    def send_sms(self, mno, msg, sid, mt=0, fl=0):
        raise NotImplementedError
    
    @abstractmethod
    def simulator(self, mno, msg, sid, mt=0, fl=0):
        raise NotImplementedError
    
    @abstractmethod
    def format_callback(self,  mno, sid, msgid, date, status):
        raise NotImplementedError


class AuthRequiredException(Exception):
    pass 
