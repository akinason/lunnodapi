
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


class AuthRequiredException(Exception):
    pass 
