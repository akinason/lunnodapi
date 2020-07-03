import os 

from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from configparser import ConfigParser 
from basedir import basedir 

config = ConfigParser()
config.read(os.path.join(basedir, 'config.ini'))
DEBUG = config.getboolean('BASE', 'DEBUG')


class Base:
    SECRET_KEY = config.get('BASE', 'SECRET_KEY')
    SENT_SMS_ACCOUNT = config.get('BASE', 'SENT_SMS_ACCOUNT')
    SALES_SMS_ACCOUNT = config.get('BASE', 'SALES_SMS_ACCOUNT')

    # email server
    MAIL_SERVER = config.get('MAIL', 'MAIL_SERVER')
    MAIL_PORT = config.get('MAIL', 'MAIL_PORT')
    MAIL_USE_TLS = config.get('MAIL', 'MAIL_USE_TLS')
    MAIL_USERNAME = config.get('MAIL', 'MAIL_USERNAME')
    MAIL_PASSWORD = config.get('MAIL', 'MAIL_PASSWORD')
    EMAIL_SENDER = config.get('MAIL', 'EMAIL_SENDER')

    # database
    DB_USERNAME = config.get('DATABASE', 'DB_USERNAME')
    DB_NAME = config.get('DATABASE', 'DB_NAME')
    DB_PASSWORD = config.get('DATABASE', 'DB_PASSWORD')
    DB_PORT = config.get('DATABASE', 'DB_PORT', fallback=5432)
    # SQLALCHEMY_DATABASE_URI = f'mysql+mysqldb://{DB_USERNAME}:{DB_PASSWORD}@localhost:3306/{DB_NAME}'
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # gearman
    GEARMAN_CLIENT_HOST_LIST = config.get('GEARMAN', 'GEARMAN_CLIENT_HOST_LIST').replace(" ", "").split(',')
    GEARMAN_WORKER_HOST_LIST = config.get('GEARMAN', 'GEARMAN_WORKER_HOST_LIST').replace(" ", "").split(',')

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
    GLOXON_APP_KEY = config.get('OAUTH', 'GLOXON_APP_KEY')
    GLOXON_APP_SECRET = config.get('OAUTH', 'GLOXON_APP_SECRET')
    
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
