import logging.handlers
from flask import Flask


app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('systems.cfg')

if not app.debug and 'MAIL_SERVER' in app.config:
    mail_handler = logging.handlers.SMTPHandler(
        mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        fromaddr='no-reply@' + app.config['MAIL_SERVER'],
        toaddrs=app.config['ADMINS'], subject='IMP Systems page error')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
