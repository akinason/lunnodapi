from concurrent.futures import ThreadPoolExecutor
import time 

import numpy as np 

from config import config
from application import db, executor
from application.models.smscenter import ShortMessage, sms_status
from application.models.smsprovider import Provider
from application.smsprovider.lib.gloxonsms import GloxonSMS


def messenger(message_id, provider_id):
    """
    Responsible for sending single messages.
    """
    shortMessage = ShortMessage.get_message_using_id(message_id)
    provider = Provider.get_provider_using_id(provider_id)
    
    gloxon = GloxonSMS(provider.username, provider.password)

    res = {}
    if config.SIMULATE_SMS_SENDING:
        res = gloxon.simulator(
            mno=shortMessage.mno, msg=shortMessage.msg, sid=shortMessage.sid, mt=shortMessage.mt, 
            fl=shortMessage.fl 
        )
    else:
        res = gloxon.send_sms(
            mno=shortMessage.mno, msg=shortMessage.msg, sid=shortMessage.sid, mt=shortMessage.mt, 
            fl=shortMessage.fl 
        )

    if res['success']:
        shortMessage.status = sms_status.sent
        shortMessage.response_time = res['response_time']
        shortMessage.provider_id = provider.id 
        shortMessage.external_id = res['message_id']
    else:
        shortMessage.status = sms_status.submitted
    
    shortMessage.attempts += 1
    db.session.add(shortMessage)
    db.session.commit()

    print(f"Message Id: {shortMessage.id}  Provider: {provider.name} Status: {shortMessage.status} Time: {time.time()}")


def _mark_provider_as_in_use(provider_id):
    provider = Provider.get_provider_using_id(provider_id)
    provider.is_in_use = True
    db.session.add(provider)
    db.session.commit()
    

def _mark_provider_as_not_in_use(provider_id):
    provider = Provider.get_provider_using_id(provider_id)
    provider.is_in_use = False 
    db.session.add(provider)
    db.session.commit()


def send_messages():
    msgs = ShortMessage.get_messages_by_status(sms_status.submitted)

    if msgs is None:
        return "No Messages" 
    
    providers = Provider.get_providers_not_in_use()
    if providers is None:
        return "No Providers"

    msgs = [m.id for m in msgs]  # We extract only the ids
    provider_count = len(providers)
    msg_count = len(msgs) 

    if provider_count > msg_count:
        providers = providers[:msg_count]

    # mark providers as in use.
    provider_ids = [p.id for p in providers]
    with ThreadPoolExecutor() as executor:
        executor.map(_mark_provider_as_in_use, provider_ids)

    provider_count = len(providers) # We re-calculate the size since it may have been sliced.

    msgs = np.array(msgs)
    msg_chunks = np.array_split(msgs, provider_count)
    msg_chunks = [m.tolist() for m in msg_chunks]

    msg_list = []
    prov_list = []
    for indx, prov in enumerate(provider_ids):
        msgs = msg_chunks[indx]
        msg_list += msgs 
        prov_list += [prov] * len(msgs)

    s = time.perf_counter()

    max_workers = config.EXECUTOR_MAX_WORKERS
    with ThreadPoolExecutor(max_workers) as executor:
        executor.map(messenger, msg_list, prov_list)
   
    with ThreadPoolExecutor(1) as executor:
        executor.map(_mark_provider_as_not_in_use, provider_ids)
    
    e = time.perf_counter()
    print(f"Send SMSes processing Done: Operation took {e - s} seconds")
    return "Done..."


def handle_callback(message_id, status, response):
    msg = ShortMessage.get_message_using_external_id(message_id)
    if msg is None:
        return False 
    
    msg.status = status 
    msg.response = str(response)
    db.session.add(msg)
    db.session.commit()
    return True