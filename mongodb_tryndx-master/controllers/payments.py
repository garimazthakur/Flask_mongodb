from services import payments
from flask import Blueprint, request, make_response, jsonify
from utils import utils
from utils.utils import token_required, token_required_param
import services
import validations
from constants import codes
from schema.admin import schema
from constants import messages
import celery


# Defining Blueprint

def payment(db, config,mail):

    BASE_URL = '/payment/'
    payment = Blueprint('payment', 'payment', __name__)


    @payment.route(BASE_URL+'stripe/gateways/', methods=['POST'])
    @utils.token_required
    def stripe_gateways():
        
        return {"0":None}



    return payment