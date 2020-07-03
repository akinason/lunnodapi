from application import db, gm_worker
from application.models.smscenter import SMSAccount 


def create_sms_account(worker, job):
    
    data = job.get('data')
    owner_id = data.get('owner_id')
    name = data.get('name')
    is_default = data.get('is_default', True)
    is_floataccount = data.get('is_floataccount', False)
    print(f"Received request to create sms account for <{name}:{owner_id}>")
    
    account = SMSAccount(owner_id=owner_id, name=name, is_default=is_default)
    account.is_floataccount=is_floataccount
    account.set_public_id()
    db.session.add(account)
    db.session.commit()
    return account.public_id 


gm_worker.register_task('smscenter.smsaccount.create', create_sms_account)
