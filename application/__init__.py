import config 
from flask import Flask 
from flask_apscheduler import APScheduler
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_executor import Executor 

from application.utils.gearman import JSONGearmanClient, JSONGearmanWorker

gm_client = JSONGearmanClient(config.Configurations.GEARMAN_CLIENT_HOST_LIST)
gm_worker = JSONGearmanWorker(config.Configurations.GEARMAN_WORKER_HOST_LIST)

app = Flask(__name__)

app.debug = config.DEBUG
if config.DEBUG:
    app.config.from_object('config.Development') 
else:
    app.config.from_object('config.Production')

db = SQLAlchemy(app)
ma = Marshmallow(app)
scheduler = APScheduler(app=app)
scheduler.start()
executor = Executor(app)


from application.account.routes import *
from application.smscenter.jobs import * 
from application.smscenter.routes import *
from application.smsprovider.routes import *
