from constants import codes, messages
from bson import ObjectId
import validations
import schema
import jwt
# from jwt import encode
import datetime
from utils.utils import SECRET_KEY
from random import *
from flask_mail import *
from utils import *
import pandas
import calculations
from collections import Counter
import json
import re
import stripe
from config.live import STRIPE_KEY


stripe.api_key=STRIPE_KEY

def retrive_customer(token):
    try:
        data = stripe.Customer.list_sources(token,object="card")
        return data
    except stripe.error.CardError as e:
        print('Status is: %s' % e.http_status)
        print('Type is: %s' % e.error.type)
        print('Code is: %s' % e.error.code)
        print('Param is: %s' % e.error.param)
        print('Message is: %s' % e.error.message)
        body = e.json_body
        err = body.get('error', {})
        return({"token":None, "message": e.error.message, "code": "400"})
    except stripe.error.RateLimitError as e:
        return({"token":None, "message": "Rate Limit Error", "code": "400"})
    except stripe.error.InvalidRequestError as e:
        return({"token":None, "message": "Invalid Parameters", "code": "400"})
    except stripe.error.AuthenticationError as e:
        return({"token":None, "message": "Card Not Authenticated", "code": "400"})
    except stripe.error.APIConnectionError as e:
        return({"token":None, "message": "Network Error", "code": "400"})
    except stripe.error.StripeError as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    except Exception as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    return({"token":None, "message": "Invalid Card Data", "code": "400"})

def set_default_card(customer_id , card_id):
    try:
        data = stripe.Customer.modify(str(customer_id),default_source=str(card_id))
        return({"token":None, "message": "Default card has been changed", "code": "200"}) 
    except stripe.error.CardError as e:
        print('Status is: %s' % e.http_status)
        print('Type is: %s' % e.error.type)
        print('Code is: %s' % e.error.code)
        print('Param is: %s' % e.error.param)
        print('Message is: %s' % e.error.message)
        body = e.json_body
        err = body.get('error', {})
        return({"token":None, "message": e.error.message, "code": "400"})
    except stripe.error.RateLimitError as e:
        return({"token":None, "message": "Rate Limit Error", "code": "400"})
    except stripe.error.InvalidRequestError as e:
        return({"token":None, "message": "Invalid Parameters", "code": "400"})
    except stripe.error.AuthenticationError as e:
        return({"token":None, "message": "Card Not Authenticated", "code": "400"})
    except stripe.error.APIConnectionError as e:
        return({"token":None, "message": "Network Error", "code": "400"})
    except stripe.error.StripeError as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    except Exception as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    return({"token":None, "message": "Invalid Card Data", "code": "400"})







def existing_customer(customer_id,token):
    try:
        data = stripe.Customer.create_source(str(customer_id),source=str(token))
        customer_data = {"card_id":data['id'],"customer_id":data['customer']}
        return({"token":customer_data, "message": "Card Added Successfully", "code": "200"})

    except stripe.error.CardError as e:
        print('Status is: %s' % e.http_status)
        print('Type is: %s' % e.error.type)
        print('Code is: %s' % e.error.code)
        print('Param is: %s' % e.error.param)
        print('Message is: %s' % e.error.message)
        body = e.json_body
        err = body.get('error', {})
        return({"token":None, "message": e.error.message, "code": "400"})
    except stripe.error.RateLimitError as e:
        return({"token":None, "message": "Rate Limit Error", "code": "400"})
    except stripe.error.InvalidRequestError as e:
        return({"token":None, "message": "Invalid Parameters", "code": "400"})
    except stripe.error.AuthenticationError as e:
        return({"token":None, "message": "Card Not Authenticated", "code": "400"})
    except stripe.error.APIConnectionError as e:
        return({"token":None, "message": "Network Error", "code": "400"})
    except stripe.error.StripeError as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    except Exception as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    return({"token":None, "message": "Invalid Card Data", "code": "400"})





def Create_customer(token,email,first_name,last_name):
    """
    Add customer to stripe
    """
    try:
        data = stripe.Customer.create(
            email=email,
            name='{} {}'.format(first_name,last_name),
            source=token
            )
        return({"token":data['id'], "message":"Customer Created Successfully", "code": "200"}) 
    except stripe.error.CardError as e:
        print('Status is: %s' % e.http_status)
        print('Type is: %s' % e.error.type)
        print('Code is: %s' % e.error.code)
        print('Param is: %s' % e.error.param)
        print('Message is: %s' % e.error.message)
        body = e.json_body
        err = body.get('error', {})
        return({"token":None, "message": e.error.message, "code": "400"})
    except stripe.error.RateLimitError as e:
        return({"token":None, "message": "Rate Limit Error", "code": "400"})
    except stripe.error.InvalidRequestError as e:
        return({"token":None, "message": "Invalid Parameters", "code": "400"})
    except stripe.error.AuthenticationError as e:
        return({"token":None, "message": "Card Not Authenticated", "code": "400"})
    except stripe.error.APIConnectionError as e:
        return({"token":None, "message": "Network Error", "code": "400"})
    except stripe.error.StripeError as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    
    except Exception as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    return({"token":None, "message": "Invalid Card Data", "code": "400"})    
   



def generate_card_token(cardnumber,expmonth,expyear,cvv):
    try:
        data= stripe.Token.create(
            card={
                "number": str(cardnumber),
                "exp_month": int(expmonth),
                "exp_year": int(expyear),
                "cvc": str(cvv),
            })
        token_id = data['id']
        card_id  = data['card']['id']
        return({"token":{"token_id":token_id,"card_id":card_id}, "message": "Token Genrated Successfully", "code": "200"})
    except stripe.error.CardError as e:
        print('Status is: %s' % e.http_status)
        print('Type is: %s' % e.error.type)
        print('Code is: %s' % e.error.code)
        print('Param is: %s' % e.error.param)
        print('Message is: %s' % e.error.message)
        body = e.json_body
        err = body.get('error', {})
        return({"token":None, "message": e.error.message, "code": "400"})
    except stripe.error.RateLimitError as e:
        return({"token":None, "message": "Rate Limit Error", "code": "400"})
    except stripe.error.InvalidRequestError as e:
        return({"token":None, "message": "Invalid Parameters", "code": "400"})
    except stripe.error.AuthenticationError as e:
        return({"token":None, "message": "Card Not Authenticated", "code": "400"})
    except stripe.error.APIConnectionError as e:
        return({"token":None, "message": "Network Error", "code": "400"})
    except stripe.error.StripeError as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    except Exception as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    return({"token":None, "message": "Invalid Card Data", "code": "400"})

def delete_card(customer_id,card_id):
    try:
        data= stripe.Customer.delete_source(customer_id,card_id)
        if data['deleted'] == True:
            return({"token":None, "message": "Card Delete Successfully.", "code": "200"})
        else:
            return({"token":None, "message": "Something went wrong", "code": "400"})
    except stripe.error.CardError as e:
        print('Status is: %s' % e.http_status)
        print('Type is: %s' % e.error.type)
        print('Code is: %s' % e.error.code)
        print('Param is: %s' % e.error.param)
        print('Message is: %s' % e.error.message)
        body = e.json_body
        err = body.get('error', {})
        return({"token":None, "message": e.error.message, "code": "400"})
    except stripe.error.RateLimitError as e:
        return({"token":None, "message": "Rate Limit Error", "code": "400"})
    except stripe.error.InvalidRequestError as e:
        return({"token":None, "message": "Invalid Parameters", "code": "400"})
    except stripe.error.AuthenticationError as e:
        return({"token":None, "message": "Card Not Authenticated", "code": "400"})
    except stripe.error.APIConnectionError as e:
        return({"token":None, "message": "Network Error", "code": "400"})
    except stripe.error.StripeError as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    except Exception as e:
        return({"token":None, "message": "Something Went Wrong", "code": "400"})
    return({"token":None, "message": "Invalid Card Data", "code": "400"})
   
def create_plan(amount_to_be_deduct, plan_name, time_interval):
    data = stripe.Plan.create(
            amount=int(amount_to_be_deduct), # Stripe accept amount in cents. For example 10 USD, provide an amount value of 1000 (i.e., 1000 cents). Thats why I multiple amount by 100.
            interval=time_interval,
            product={
                "name": plan_name
            },
            currency="usd"
        )
    return data

def convert_to_unix_timestamp(plan_create_date, billing_cycle_tag, current_year):
    from datetime import datetime
    unix_plan_create_date = datetime.utcfromtimestamp(plan_create_date).strftime('%Y-%m-%d')
    date_plan_create_date = datetime.strptime(unix_plan_create_date, '%Y-%m-%d')
    month_plan_create_date = int(date_plan_create_date.strftime("%m")) + 1
    billing_cycle_anchor_date = current_year + '-' + str(month_plan_create_date) + '-' + billing_cycle_tag
    billing_cycle_anchor_tag = int(datetime.strptime(billing_cycle_anchor_date, '%Y-%m-%d').timestamp())
    return billing_cycle_anchor_tag


def create_subscription(customer_id, plan_list, billing_cycle_anchor_tag):
    subscription_dict = []
    #creating subscription of plans
    for plan_id in plan_list:
        data = stripe.Subscription.create(
                customer= customer_id,
                items=[
                    {
                        'plan': plan_id
                    }
                ],
                billing_cycle_anchor=billing_cycle_anchor_tag,
                proration_behavior='none',
            )
        subscription_dict.append(data['id'])
    return subscription_dict


def create_payment_charge(tokenid,amount,description, plan_type):
    # print(int(float(amount)*100))
    from datetime import datetime
    try:
        payment = stripe.Charge.create(
            amount=(int(float(amount)*100)),                  # convert amount to cents
            currency='usd',
            description=description,
            customer=tokenid,
            )
        payment_check = payment['paid']
        if payment_check == True:
            if plan_type == "monthly":
                monthly_stripe_plan = create_plan((int(float(amount)*100)), "monthly subscription", "month")
                current_date = (datetime.utcnow()).strftime("%d")
                current_year = (datetime.utcnow()).strftime("%Y")
                billing_cycle_anchor_tag_monthly = convert_to_unix_timestamp(monthly_stripe_plan['created'], current_date, current_year)
                create_subscription(tokenid, [monthly_stripe_plan['id']], str(billing_cycle_anchor_tag_monthly))
            if plan_type == "yearly":
                yearly_stripe_plan = create_plan((int(float(amount)*100)), "annually subscription", "year")
                current_date = (datetime.utcnow()).strftime("%d")
                current_year = (datetime.utcnow()).strftime("%Y")
                billing_cycle_anchor_tag_yearly = convert_to_unix_timestamp(yearly_stripe_plan['created'], current_date, current_year)
                create_subscription(tokenid, [yearly_stripe_plan['id']], str(billing_cycle_anchor_tag_yearly))
                
            return ({"payment_check":True,"amount":payment['amount'],"transaction_id":payment['balance_transaction'],"message":"Payment Successful","code":"200"})
        else:
            return ({"payment_check":False,"message":"Payment Failed","code":"400"})


    # except stripe.error.CardError as e:
        print('Status is: %s' % e.http_status)
        print('Type is: %s' % e.error.type)
        print('Code is: %s' % e.error.code)
        print('Param is: %s' % e.error.param)
        print('Message is: %s' % e.error.message)
        body = e.json_body
        err = body.get('error', {})
        return({"payment_check":False, "message": e.error.message, "code": "400"})
    except stripe.error.RateLimitError as e:
        return({"payment_check":False, "message": "Rate Limit Error", "code": "400"})
    except stripe.error.InvalidRequestError as e:
        return ({"payment_check":False, "message": "Invalid Request", "code": "400"})
    except stripe.error.AuthenticationError as e:
        return({"payment_check":False, "message": "Card Not Authenticated", "code": "400"})
    except stripe.error.APIConnectionError as e:
        return({"payment_check":False, "message": "Network Error", "code": "400"})
    except stripe.error.StripeError as e:
        return({"payment_check":False, "message": "Something Went Wrong", "code": "400"})
    except Exception as e:
        return({"payment_check":False, "message": "Something Went Wrong", "code": "400"})
    return({"payment_check":False, "message": "Invalid Card Data", "code": "400"})


