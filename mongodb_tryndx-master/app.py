from re import template
import config
from flask import Flask
from flask_pymongo import PyMongo as DB
import controllers
from flask_mail import *
from random import *
from flask_cors import CORS
# from OpenSSL import SSL

# context = SSL.Context(SSL.PROTOCOL_TLSv1_2)
# context.use_privatekey_file('/etc/letsencrypt/live/python.webdevelopmentsolution.net/privkey.pem')
# context.use_certificate_file('/etc/letsencrypt/live/python.webdevelopmentsolution.net/fullchain.pem') 



app = Flask(__name__, template_folder="mails/verify_login/")
app.config['JSON_SORT_KEYS'] = False
cors = CORS(app, resources={r"/*": {"origins": "*"}})
app.config['CORS-HEADERS'] = 'Content-Type'
app.config['MONGO_URI'] = config.local.DB_URI
mongo = DB(app)

app.config["MAIL_SERVER"]='smtp.gmail.com'
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = 'tryndx.com@gmail.com'
app.config['MAIL_PASSWORD'] = 'W3CanMak3it$'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


# Registering the Blueprint defined in controller.admin
app.register_blueprint(controllers.admin.admin(mongo.db, config.local,mail))
app.register_blueprint(controllers.user.user(mongo.db,config.local,mail))
app.register_blueprint(controllers.payments.payment(mongo.db,config.local,mail))

if __name__ == '__main__':
    # app.run(host="0.0.0.0", port=3082, debug=True, ssl_context=("/etc/letsencrypt/live/python.webdevelopmentsolution.net/fullchain.pem", "/etc/letsencrypt/live/python.webdevelopmentsolution.net/privkey.pem"))  # Running the Application.
    app.run(host="0.0.0.0", port=3082, debug=True)  # Running the Application.c

