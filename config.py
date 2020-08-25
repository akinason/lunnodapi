import os 

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from configparser import ConfigParser 
from basedir import basedir 

_config = ConfigParser()
_config.read(os.path.join(basedir, 'config.ini'))
DEBUG = _config.getboolean('BASE', 'DEBUG')


class Base:
    SECRET_KEY = _config.get('BASE', 'SECRET_KEY')
    SENT_SMS_ACCOUNT = _config.get('BASE', 'SENT_SMS_ACCOUNT')
    SALES_SMS_ACCOUNT = _config.get('BASE', 'SALES_SMS_ACCOUNT')
    BACKEND_URL = _config.get('BASE', "BACKEND_URL")
    FRONTEND_URL = _config.get('BASE', "FRONTEND_URL")
    
    # email server
    MAIL_SERVER = _config.get('MAIL', 'MAIL_SERVER')
    MAIL_PORT = _config.get('MAIL', 'MAIL_PORT')
    MAIL_USE_TLS = _config.get('MAIL', 'MAIL_USE_TLS')
    MAIL_USERNAME = _config.get('MAIL', 'MAIL_USERNAME')
    MAIL_PASSWORD = _config.get('MAIL', 'MAIL_PASSWORD')
    EMAIL_SENDER = _config.get('MAIL', 'EMAIL_SENDER')

    # database
    DB_USERNAME = _config.get('DATABASE', 'DB_USERNAME')
    DB_NAME = _config.get('DATABASE', 'DB_NAME')
    DB_PASSWORD = _config.get('DATABASE', 'DB_PASSWORD')
    DB_PORT = _config.get('DATABASE', 'DB_PORT', fallback=5432)
    # SQLALCHEMY_DATABASE_URI = f'mysql+mysqldb://{DB_USERNAME}:{DB_PASSWORD}@localhost:3306/{DB_NAME}'
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # gearman
    GEARMAN_CLIENT_HOST_LIST = _config.get('GEARMAN', 'GEARMAN_CLIENT_HOST_LIST').replace(" ", "").split(',')
    GEARMAN_WORKER_HOST_LIST = _config.get('GEARMAN', 'GEARMAN_WORKER_HOST_LIST').replace(" ", "").split(',')

     # apscheduler
    JOBS = []
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
    }

    SCHEDULER_EXECUTORS = {
        'default': ThreadPoolExecutor(),
        'processpool': ProcessPoolExecutor()
    }

    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 100
    }

    SCHEDULER_API_ENABLED = False

    # Oauth
    GLOXON_APP_KEY = _config.get('OAUTH', 'GLOXON_APP_KEY')
    GLOXON_APP_SECRET = _config.get('OAUTH', 'GLOXON_APP_SECRET')
    
    # Threading
    EXECUTOR_MAX_WORKERS = int(_config.get('BASE', 'EXECUTOR_MAX_WORKERS'))
    SIMULATE_SMS_SENDING = _config.getboolean('BASE', 'SIMULATE_SMS_SENDING')


class Development(Base):
    DEBUG = True  

class Production(Base):
    DEBUG = False


if DEBUG:
    class Configurations(Development):
        pass
else:
    class Configurations(Production):
        pass

config = Development() if DEBUG else Production()
