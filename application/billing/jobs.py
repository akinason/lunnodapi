from flask import render_template

from config import config
from datetime import datetime 
from application import gm_worker 
from application.billing.manager import Manager
from application.models.billing import BillingTransaction
from application.utils.mailer import Message, Mail 


def print_statement(statement):
    print(datetime.utcnow(), statement)
    

def parse_callback(worker, job):
    pg_name = job.data.get("pg_name")
    data = job.data.get("data")
    manager = Manager()
    res = manager.parse_callback(pg_name, data)
    print_statement("Finished parsing callback for %s. Response: %s" % (pg_name, res))


def verify_payment(worker, job):
    txn_id = job.data.get("transaction_id")
    manager = Manager()
    res = manager.verify_payment(txn_id)
    print_statement("Finished verifying payment transaction # %s. Response: %s" % (txn_id, res))

def send_sms_sales_email(worker, job):
    txn_id = job.data.get("transaction_id")
    txn = BillingTransaction.get_transaction_using_id(txn_id)
    body = f""" 
    Your SMS account has been reloaded with {txn.quantity} SMS credits, following your recent purchase. 

    Reference: {txn.reference}
    Quantity:  {txn.quantity} SMS credits
    Account: {txn.smsaccount.name} ({txn.smsaccount.public_id})
    Account Balance: {txn.smsaccount.balance} SMS Credits
    Payment Method: {txn.payment_gateway.name}

    Thanks for Trusting Gloxon Empire
    """

    user = txn.user 
    sender = f"{config.EMAIL_SENDER} <{config.MAIL_USERNAME}>"
    recipient = txn.user.email
    msg = Message(sender=sender, recipients=recipient, subject="SMS Account Refilled", body=body, html=False)
    mail = Mail(msg)
    r = mail.send()
    print_statement(f"Sending account refill email for txn # {txn.id}. Response: {r}")


gm_worker.register_task("billing.parse_callback", parse_callback)
gm_worker.register_task("billing.verify_payment", verify_payment)
gm_worker.register_task("billing.sms_sales_email", send_sms_sales_email)

