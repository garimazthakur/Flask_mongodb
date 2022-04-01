from os import remove
from constants import codes, messages
from bson import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash
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
from flask import render_template
from flask_mail import Message
from . import payments
import plaid
from plaid.api import plaid_api
import requests
import json
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': "6124a9928fc32f0010278d45",
        'secret': "4fb68f2fcf2fdf2c3b1f8602421194",
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

headers={"Content-Type":"application/json"}




def signup(db, setObj, mail):
    validateResp = validations.admin.validateAdmin(setObj, schema.user.schema)
    if validateResp == {}:
        unique = validations.user.isUnique(db, setObj)
        if unique == True:
            current_id = db.control.find_one({},{"UID":1,"_id":0})
            a = str((datetime.datetime.now()))
            a = a.replace('-', '')
            a = a.replace(' ', '')
            a = a.replace('.', '')
            a = a.replace(':', '')
            a = a[7:16]
            if current_id == None or current_id == {}:
                db.control.insert({"UID":1})
                UID = "1"+ a
                setObj['UID'] = UID
            else:
                UID = current_id['UID'] + 1
                db.control.update_one({"UID":current_id['UID']},{"$set":{"UID":UID}})
                UID = str(UID) + a
                setObj['UID'] = UID
            setObj['password'] = generate_password_hash(setObj['password'])
            setObj['isPasswordSet'] = True
            setObj['isDetailFilled'] = False
            setObj['full_name'] = setObj["firstName"] + " " + setObj["lastName"]
            setObj['isCSVUploaded'] = False
            setObj['isActive'] = True
            setObj['isPrivate'] = False
            setObj['isMentor'] = False
            setObj['mentor_request'] = 0
            setObj['trader_request'] = 0
            setObj['isVerifiedTrader'] = False
            setObj['is_social'] = False
            setObj['social_type'] = None
            setObj['signup_otp_vertified'] = False
            setObj['created_at'] = datetime.datetime.utcnow()
            setObj['is_subscribed'] = False
            if 'country_code' not in setObj:
                setObj['country_code'] = None
            doc = db.users.insert_one(setObj)
            doc = db.users.find_one({"_id": doc.inserted_id})


            doc['_id'] = str(doc['_id'])
            r = utils.generateLinkUser(db, setObj, mail)
            return {"status": codes.OK, "result": doc, "message": "User Created Successfully"}
        else:
            message = unique[0] + ' Already Exist' 
            return {"status": codes.BAD_REQUEST, "result": "You are entering data, which already exist", "message": message}
    else:
        key = list(validateResp.keys())
        message = key[0].capitalize() + ' is invalid.'
        return {"status": codes.BAD_REQUEST, "result": validateResp , "message":message}


def verifyOTP(db, setObj):
    otp = setObj['otp']
    doc = db.resetToken.find_one({"email":setObj['email']})
    actual_otp = doc['token']
    time = doc['exp']
    if str(actual_otp) == str(otp):
        if time >= datetime.datetime.utcnow():
            doc1 = db.users.update_one({"email":setObj["email"]},{"$set":{"isActive":True,"signup_otp_vertified":True}})
            doc2 = db.resetToken.update_one({"email":setObj["email"]},{"$set":{"token":None,"exp":None}})
            if doc1:
                return {"status": codes.OK, "result": "OTP Verified Succesfully", "message": messages.OTP_VERIFIED}
        else:
            return {"status": codes.BAD_REQUEST, "result": "OTP has expired", "message": messages.OTP_EXPIRED}
    else:
        return {"status": codes.BAD_REQUEST, "result": "Please Enter Correct OTP", "message":messages.INVALID_OTP}

        
def forgotPassword(db,setObj, mail):
    doc = db.users.find_one({'username':setObj['email']})
    if doc:
        doc = doc['is_social']
    else:
        doc = False
    if doc == False:
        r = utils.generateLinkUser(db, setObj, mail)
        return r
    else:
        return {"status": codes.BAD_REQUEST, "result": "Social User connot use this feature", "message":messages.SOCIAL_CONNOT_USE_FORGOT_PASSWORD}

def authenticate_otp(db, setObj):
    otp = setObj['otp']
    doc = db.resetToken.find_one({"email":setObj['email']})
    actual_otp = doc['token']
    time = doc['exp']
    if str(actual_otp) == str(otp):
        if time >= datetime.datetime.utcnow():
            doc = db.users.update_one({"email":setObj['email']},{"$set":{"otp_verfied":True}})
            username = db.users.find_one({"email":setObj['email']})['username']
            doc2 = db.resetToken.update_one({"email":setObj["email"]},{"$set":{"token":None,"exp":None}})
            return {"status": codes.OK, "result": username, "message": messages.OTP_VERIFIED}
        return {"status": codes.BAD_REQUEST, "result": "OTP has expired", "message": messages.OTP_EXPIRED}
    return {"status": codes.BAD_REQUEST, "result": "Please Enter Correct OTP", "message":messages.INVALID_OTP}


def change_pass_after_otp(db, setObj):
    user = db.users.find_one({"username":setObj['username']},{'_id':0})['otp_verfied']
    if user == True:
        pass_hash = generate_password_hash(setObj['password'])
        doc = db.users.update_one({"username":setObj["username"]},{"$set":{"password":pass_hash}})
        if doc:
            doc = db.users.update_one({"username":setObj['username']},{"$set":{"otp_verfied":False}})
            return {"status": codes.OK, "result": "password changed successfully", "message": messages.PASSWORD_RESET_SUCCESSFUL}
        return {"status": codes.BAD_REQUEST, "result": "Password not changed", "message": messages.PASSWORD_RESET_UNSUCCESSFUL}

    return {"status": codes.BAD_REQUEST, "result": "OTP not verified", "message":messages.RESEND_OTP}


def signin(db,setObj):
    res = {"Status":"Success"}
    doc = db.users.find_one({"username": setObj['username']})
    if doc is None:
        return {"status": codes.BAD_REQUEST, "result": 'USER NOT FOUND', "message": messages.USER_DOES_NOT_EXIST, "token":''}
    else:
        res["UID"] = doc["UID"]
        keys = list(doc.keys())
        if 'email' in keys:
            res['email'] = doc['email']
        if 'phone' in keys:
            res['phone'] = doc['phone']
        if 'firstName' in keys:
            res['firstName'] = doc['firstName']
        if 'lastName' in keys:
            res['lastName'] = doc['lastName']
        if 'social_type' in keys:
            res['social_type'] = doc['social_type']
        if doc['isPasswordSet'] == True or doc['isPasswordSet'] == 'true':
            res['isPasswordSet'] = True
        if doc['isDetailFilled'] == True or doc['isDetailFilled'] == 'true':
            res['isDetailFilled'] = True
        if doc['isCSVUploaded'] == True or doc['isCSVUploaded'] == 'true':
            res['isCSVUploaded'] = True
        res["profilePic"] = doc["profilePic"] if "profilePic" in doc else None
        if 'is_social' not in keys:
            doc['is_social'] = False
        if doc['isActive'] == True:
            if "signup_otp_vertified" not in keys:
                doc["signup_otp_vertified"] = True
            if doc["signup_otp_vertified"] == False:
                return {"status": codes.OK, "result": res['email'], "message": messages.VERIFICATION_PENDING, "token":''}
            if doc['is_social'] == False:
                if check_password_hash(doc['password'],setObj['password']) == True:
                    token = jwt.encode(
                        {'id': str(doc['_id']), 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=3000)}, SECRET_KEY,
                        algorithm='HS256')
                    doc['_id'] = str(doc['_id'])
                    if type(token) == bytes :
                        token = token.decode("ascii")
                    return {"status": codes.OK, "result": res, "message": messages.USER_LOGGEDIN_SUCCESSFULLY, "token": token}
                else:
                    return {"status": codes.BAD_REQUEST, "result": 'PLEASE ENTER CORRECT PASSWORD', "message": messages.INCORRECT_PASSWORD, "token":''}
            else:
                token = jwt.encode(
                        {'id': str(doc['_id']), 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=3000)}, SECRET_KEY,
                        algorithm='HS256')
                doc['_id'] = str(doc['_id'])
                if type(token) == bytes :
                    token = token.decode("ascii")
                    return {"status": codes.OK, "result": res, "message": messages.USER_LOGGEDIN_SUCCESSFULLY, "token": token}
                return {"status": codes.OK, "result": res, "message": messages.USER_LOGGEDIN_SUCCESSFULLY, "token": token}
        else:
            return {"status": codes.BAD_REQUEST, "result": "User is Inactive", "message": messages.USER_IS_INACTIVE, "token": ""}

def social_signup(db, setObj):
    social=True
    UID = None
    unique = validations.user.isUnique(db, setObj, UID, social)
    if unique == True:
        current_id = db.control.find_one({},{"UID":1,"_id":0})
        a = str((datetime.datetime.now()))
        a = a.replace('-', '')
        a = a.replace(' ', '')
        a = a.replace('.', '')
        a = a.replace(':', '')
        a = a[7:16]
        if current_id == None or current_id == {}:
            db.control.insert({"UID":1})
            UID = "1"+ a
            setObj['UID'] = UID
        else:
            UID = current_id['UID'] + 1
            db.control.update_one({"UID":current_id['UID']},{"$set":{"UID":UID}})
            UID = str(UID) + a
            setObj['UID'] = UID
        setObj['username'] = setObj['username']
        setObj['email'] = setObj['username']
        setObj['password'] = None
        setObj['isPasswordSet'] = True
        setObj['isDetailFilled'] = False
        setObj['full_name'] = setObj["firstName"] + " " + setObj["lastName"]
        setObj['isCSVUploaded'] = False
        setObj['isActive'] = True
        setObj['isPrivate'] = False
        setObj['isMentor'] = False
        setObj['mentor_request'] = 0
        setObj['trader_request'] = 0
        setObj['isVerifiedTrader'] = False
        setObj['is_social'] = True
        setObj['created_at'] = datetime.datetime.utcnow()
        setObj['is_subscribed'] = False
        if 'country_code' not in setObj:
                setObj['country_code'] = None
        doc = db.users.insert_one(setObj)
        doc = db.users.find_one({"_id": doc.inserted_id})
        doc['_id'] = str(doc['_id'])
        body = {"username":setObj['username']}
        # print(signin(db, body))
        return signin(db, body)
    else:
        # body = {"username":setObj['username']}
        # print([signin(db, body)])
        # return signin(db, body)
        message = unique[0] + ' Already Exist'
        return {"status": codes.BAD_REQUEST, "result": "You are entering data, which already exist", "message": message, "token":""}
 
def check_user(db,id):
    user = db.users.find_one({"_id":ObjectId(id)})
    if user:
        if 'is_subscribed' in user:
            is_subscribed = user['is_subscribed']
        else:
            is_subscribed = False
        if 'created_at' in user:
            created_at = user['created_at']
        else:
            created_at = datetime.datetime.utcnow() - datetime.timedelta(days=100)
        if created_at + datetime.timedelta(days=7) > datetime.datetime.utcnow() or is_subscribed == True :
            return {"status": codes.OK, "result": "User Exist", "message": messages.USER_DETAILS_FETCHED}
        else:
            return {"status": codes.OK, "result": "User Must take Subscription", "message": messages.USER_DETAILS_FETCHED}

    else:
        return {"status": codes.BAD_REQUEST, "result": "User Does Not Exist", "message": messages.USER_DELETED}





def fillDetails(db,setObj, id):
    UID = db.users.find_one({"_id":ObjectId(id)},{"_id":0,"UID":1})["UID"]
    setObj['isEmailVerified'] = 'false'
    setObj['full_name'] = setObj["firstName"] + " " + setObj["lastName"]
    validResp = validations.user.validateUser(setObj,schema.user.schema)
    if validResp == {}:
        isUnique = validations.user.isUnique(db,setObj,UID)
        if isUnique == True:
            #setObj.update(db.users.find_one({"_id":ObjectId(id)}, {"_id":0}))
            setObj['isDetailFilled'] = True
            doc = db.users.update({"_id":ObjectId(id)},{"$set":setObj})
            doc1 = db.users.find_one({"UID":UID},{"_id":0,"profilePic":1,"UID":1})
            if "profilePic" in doc1:
                setObj.update({"profilePic": doc1["profilePic"]})
            if 'UID' in doc1:
                setObj['UID'] = doc1['UID']


            return {"status": codes.OK, "result": setObj, "message": messages.USER_DEATAILS_ADDED_SUCCESSFULLY}
        else:
            message = isUnique[0] + ' Already Exists'
            return {"status": codes.BAD_REQUEST, "result": isUnique, "message": message}
    else:
        key = list(validResp.keys())
        message = key[0].capitalize() + ' is invalid.'
        return {"status": codes.BAD_REQUEST, "result": validResp, "message": message}

def resetPass(db, setObj, id):
    isValid = validations.user.validateUser(setObj,schema.user.schema)
    if isValid == {}:
        setObj['password'] = generate_password_hash(setObj['password'])
        setObj['isPasswordSet'] = 'true'
        doc = db.users.update({"_id":ObjectId(id)}, {'$set':{'password':setObj['password'], 'isPasswordSet': setObj['isPasswordSet']  }})
        if doc['n']==1:
            return {"status": codes.OK, "result": "Password Updated Successfully",
                    "message": messages.PASSWORD_RESET_SUCCESSFUL}
        else:
            return {"status": codes.INTERNAL_SERVER_ERROR, "result": "Password Not Updated",
                    "message": messages.PASSWORD_RESET_UNSUCCESSFUL}
    else:
        return {"status": codes.BAD_REQUEST, "result": isValid,
                "message": messages.PASSWORD_RESET_UNSUCCESSFUL}



def generateOTP(setObj,mail,db,id):
    otp = randint(000000, 999999)
    email = setObj['email']
    msg = Message('Email Verification for TRYNDx', sender='username@gmail.com', recipients=[email])
    # msg.body = "Greeting from TryndX, Here is your OTP for Email Verification" + str(otp)
    msg.html=render_template("/mails/verify_login/index2.html")
    mail.send(msg)
    doc = db.users.update({"_id": ObjectId(id)}, {"$set": {"OTP": otp,'exp': datetime.datetime.utcnow()
                                                                             + datetime.timedelta(minutes=1)}
                                                  },False, True)
    if doc:
        return {"status": codes.OK, "result": 'OTP has been sent to the mentioned Email ', "message": messages.OTP_SENT}
    else:
        return {"status": codes.BAD_REQUEST, "result": 'There was some problem while sending the email', "message": messages.SOME_ERROR_OCCURED}


def verify_OTP(db,setObj,id):
    otp = int(setObj['otp'])
    a = db.users.find_one({'_id':ObjectId(id)},{"OTP":1,"exp":1, "_id":0})
    if otp == a['OTP'] and (a['exp'] > datetime.datetime.utcnow()):
        doc = db.users.update({"_id": ObjectId(id)}, {"$set": {"isEmailVerified": True}},False, True)
        return {"status": codes.OK, "result": 'Email has been verified', "message": messages.VALIDATION_COMPLETED}
    else:
        return {"status": codes.OK, "result": 'Please Enter a correct OTP', "message": messages.OTP_EXPIRED}
        

def update(db, setObj, id):
    setObj, bank_data = get_bank_data(setObj)


    if "firstName" in setObj and "lastName" in setObj:
        setObj['full_name'] = setObj["firstName"] + " " + setObj["lastName"]

    if len(setObj) != 0:
        if "mentor_request" in setObj:
            # print(type(setObj["mentor_request"]))
            if int(setObj["mentor_request"]) == 2:
                setObj["isMentor"] = True
        if "trader_request" in setObj:
            if int(setObj["trader_request"]) == 2:
                setObj["isVerifiedTrader"] = True
        doc = db.users.update({"_id": ObjectId(id)}, {"$set":setObj})
    if len(bank_data) != 0:
        UID = db.users.find_one({"_id":ObjectId(id)},{"_id":0,"UID":1})["UID"]
        bank_data["UID"] = UID
        existing_bank_detail = db.bankDetails.find_one({"UID":UID})
        if existing_bank_detail is not None:
            doc1 = db.bankDetails.update({"UID":UID},{"$set":bank_data})
        else:
            doc1 = db.bankDetails.insert(bank_data)
    UID = db.users.find_one({"_id":ObjectId(id)},{"_id":0,"UID":1})["UID"]
    doc2 = db.users.find_one({'UID':UID},{'_id':0})
    return {"status": codes.OK, "result": doc2, "message" : messages.USER_UPDATED_SUCCESSFULLY}
    
def get_bank_data(data):
    bank_details = {}
    keys = list(data.keys())
    if "bank_name" in keys:
        bank_details.update({"bank_name":data["bank_name"]})
        del data["bank_name"]

    if "account_number" in keys:
        bank_details.update({"account_number":data["account_number"]})
        del data["account_number"]

    if "iban_number" in keys:
        bank_details.update({"iban_number":data["iban_number"]})
        del data["iban_number"]

    if "swift_code" in keys:
        bank_details.update({"swift_code":data["swift_code"]})
        del data["swift_code"]

    return data, bank_details

def savecsvInDB(db,df,id):
    UID = db.users.find_one({"_id":ObjectId(id)},{"_id":0,"UID":1})['UID']
    
    entry_amount = 0
    percentage_change=[]
    entry_csvamount = []
    exit_amount = []
    balance = []
    p_l = []
    ammount = 0
    df = df.iloc[::-1]
    count = 0
    for i in df["AMOUNT"]:
        ammount = ammount+float(i)
        if count != 0:
            entry_csvamount.append(balance[count-1])
            exit_amount.append(float(ammount))
            balance.append(float(ammount))
            p_l.append(float(i))
            percentage_change.append(round((p_l[count]/balance[count-1])*100, 2))
        else:
            entry_csvamount.append(0.0)
            exit_amount.append(float(i))
            balance.append(float(i))
            p_l.append(0.0)
            percentage_change.append(0)
            entry_amount = float(i)
        count = count+1
    df["p&l"] = p_l
    df["balance"]=balance
    df["percentage_changes"]=percentage_change
    df["entry_amount"] = entry_csvamount
    df["exit_amount"] = exit_amount
    # print(df)
    headers = calculations.user.find_headers(df)
    for ind in df.index:
        data = {}
        data['UID'] = UID
        data['setup'] = None
        data['entryLevel'] = None
        data['emotion'] = None
        data['side'] = None
        data['comments'] = None
        for header in headers:
            data[header] = str(df[header][ind])

        if float(data['AMOUNT']) > 0:
            data['profit'] = data['AMOUNT']
            data["loss"] = None
        else:
            data["profit"] = None
            data['loss'] = data['AMOUNT']

        if float(data['percentage_changes']) > 0:
            data['win_percentage'] = data['percentage_changes']
            data['loss_percentage'] = None
        else:
            data['win_percentage'] = None
            data['loss_percentage'] = data['percentage_changes']
        doc = db.transactions.insert(data)
    return 'True'

def uploadCSV(db,setObj,id):
    setObj['isCSVUploaded'] = 'true'
    doc = db.users.update_one({"_id":ObjectId(id)},{"$set": {"CSV":setObj['CSV'],"isCSVUploaded": True}})
    if doc:
        return {"status": codes.OK, "result": 'File Uploaded Successfully', "message": messages.FILE_UPLOADED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST, "result": 'File not uploaded',
                "message": messages.SOME_ERROR_OCCURED}


def fetchFileLoc(db,id):
    doc = db.users.find_one({"_id":ObjectId(id)})
    # for d in doc:
    #     print(d)
    return doc['UID']

def file_query(db,setObj,id):
    ID = db.users.find_one({'_id':ObjectId(id)},{"UID":1,"username":1,"firstName":1})
    QID = db.control.find_one({},{"QID":1,"_id":0})
    a = str((datetime.datetime.now()))
    a = a.replace('-', '')
    a = a.replace(' ', '')
    a = a.replace('.', '')
    a = a.replace(':', '')
    a = a[7:16]
    if QID == {}:
        doc = db.control.find_one({},{"_id":0,"UID":1})
        doc1 = db.control.update({"UID":doc["UID"]},{"$set":{"QID":1}})
        QID['QID'] = 1
    q = db.control.find()
    r = []
    for i in q:
        r.append(i)
    setObj['QID'] = str(QID['QID'] + 1) + a
    
    #print(setObj['QID']
    setObj['UID'] = ID['UID']
    setObj['username'] = ID['username']
    setObj['firstName'] = ID['firstName']
    setObj['Status'] = 'OPEN'
    setObj['DATE'] = str(datetime.date.today())
    setObj['Comment'] = ''
    res = db.control.update({},{"QID":QID['QID'] + 1})
    doc = db.userQuery.insert(setObj)
    if doc:
        return {"status": codes.OK, "result": 'Your Query has been sent to the admin',"message": messages.QUERY_SENT_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST, "result": 'Query not sent',"message": messages.SOME_ERROR_OCCURED}


def streak(a):
  res = {}
  prev_sign = utils.getSign(a[0])
  win_streak = 0
  loss_streak = 0
  already_in_streak = False
  for i in range(1,len(a)):
    next_sign = utils.getSign(a[i])
    if prev_sign == next_sign:
      if next_sign == '-' and already_in_streak == False:
        loss_streak+=1
        already_in_streak = True
      elif next_sign== '+' and already_in_streak == False:
        win_streak+=1
        already_in_streak = True
    else:
      already_in_streak = False
    prev_sign = next_sign
  res['win_streak'] = win_streak
  res['loss_streak'] = loss_streak
  res['win_streak_percentage'] = round((win_streak/(win_streak+loss_streak))*100, 2) if win_streak+loss_streak != 0 else 0
  res['loss_streak_percentage'] = round((loss_streak/(win_streak+loss_streak))*100, 2) if win_streak+loss_streak != 0 else 0 
  return res


def largest_smallest_streak(a):
  if len(a) > 1:  
    res = {}
    loss_streak = []
    profit_streak = []
    postives = []
    negatives = []
    i=0
    if a[-1] > 0 and a[-2] > 0:
        a.append(-1)
    elif a[-1] < 0 and a[-2] < 0:
        a.append(1)
    for data in a:
        if float(data) >= 0:
            if len(negatives)!=0:
                negatives=[]
                postives.append(float(data))
            else:
                if len(a) != i+1:
                    if float(a[i+1]) < 0:
                        if len(postives) != 0:
                            postives.append(float(data))
                            profit_streak.append(sum(postives))
                            postives = []
                        else:
                            pass
                    else:
                        postives.append(float(data))
        else:
            if len(postives) != 0:
                postives = []
                negatives.append(float(data))
            else:
                if len(a) != i+1:
                    if float(a[i+1]) > 0:
                        if len(negatives) != 0:
                            negatives.append(float(data))
                            loss_streak.append(sum(negatives))
                            negatives = []
                        else:
                            pass
                    else:
                        negatives.append(float(data))
        i = i+1
    res['totalProfitInWinStreak'] = round(sum(profit_streak),2)
    res['totalLossInLossStreak'] = round(sum(loss_streak),2)
    res['largest_profit_in_win_streak'] = max(profit_streak)
    res['largest_profit_percentage_in_win_streak'] = round((max(profit_streak)/round(sum(profit_streak),2))*100, 2) if sum(profit_streak) != 0 else 0
    res['largest_loss_percentage_in_win_streak'] = round((max(profit_streak)/round(sum(loss_streak),2))*100, 2) if sum(loss_streak) != 0 else 0
    res['largest_loss_in_loss_streak'] = min(loss_streak) if loss_streak != [] else 0
   
  else:
    res = {}
    res['totalProfitInWinStreak'] = 0
    res['totalLossInLossStreak'] = 0
    res['largest_profit_in_win_streak'] = 0
    res['largest_profit_percentage_in_win_streak'] = 0
    res['largest_loss_percentage_in_win_streak'] = 0
    res['largest_loss_in_loss_streak'] = 0
    
  return res


def getProfileInfo(db, id):
    doc = db.users.find_one({"_id":ObjectId(id)},{"_id":0,"password":0})
    if 'email' not in doc:
        doc['email'] = doc['username']
    if doc:
        bank_details = db.bankDetails.find_one({"UID":doc['UID']},{"_id":0})
        if bank_details:
            doc['bank_details'] = bank_details
        else:
            doc['bank_details'] = {}
        return {"status": codes.OK, "result": doc,"message": messages.USER_DETAILS_FETCHED}
    else:
        return {"status": codes.BAD_REQUEST, "result": 'user does not exist',"message": messages.SOME_ERROR_OCCURED}


def follow(db,setObj,id):
    doc = db.users.find_one({"_id":ObjectId(id)},{"UID":1,"_id":0})
    UID = doc["UID"]
    unique = db.followers.find_one({"UID":setObj["UID"],"followingID":UID})
    if unique is None:
        isPrivate = db.users.find_one({"UID":setObj["UID"]},{"_id":0,"isPrivate":1})
        isPrivate = False
        if isPrivate == False:
            res = db.followers.insert({"UID":setObj["UID"],"followingID":UID})
            notificationdata_sender = {}
            notificationdata_sender['UID'] = UID
            doc1 = db.users.find_one({"UID":setObj["UID"]},{"_id":0, "firstName":1, "lastName":1})
            notificationdata_sender["desc"] = "You Started Following"+" "+doc1["firstName"] + " " + doc1["lastName"]
            notificationdata_sender["isRead"] = False
            doc2 = db.notifications.insert(notificationdata_sender)

            notificationdata_receiver = {}
            notificationdata_receiver["UID"] = setObj["UID"]
            resv1 = db.users.find_one({"UID":UID},{"_id":0, "firstName":1, "lastName":1})
            notificationdata_receiver["desc"] = doc1["firstName"] + " " + doc1["lastName"]+" "+"Started Following You"
            notificationdata_receiver["isRead"] = False
            resv2 = db.notifications.insert(notificationdata_receiver)

            return {"status": codes.OK, "result": "User Followed Successfully","message": messages.FOLLOWED_SUCCESSFULLY}
        else:
            res = db.followRequests.insert({"UID":setObj["UID"],"followingID":UID})
            return {"status": codes.OK, "result": "Follow request sent successfully","message": messages.REQUEST_SENT_SUCCESSFULLY}
    else:
        return {"status": codes.OK, "result": "User is Already Followed", "message": messages.USER_ALREADY_FOLLOWED}


def getFollowing(db,offset,limit,id):
    try:
        doc = db.users.find_one({"_id": ObjectId(id)}, {"UID": 1, "_id": 0})
        UID = doc["UID"]
        stating_id = db.followers.find({"followingID":UID}, {}).sort('_id', -1)
        total_count = stating_id.count()
        last_id = stating_id[offset]["_id"]
        res = db.followers.find({"_id":{"$lte" : last_id },"followingID":UID},{"UID":1,"_id":0}).sort('_id', -1).limit(limit)
    except Exception as e:
        res = []
        total_count = 0
    result = []
    for i in res:
        d = db.users.find_one({"UID":i["UID"]},{"_id":0,"firstName":1,"lastName":1,"UID":1,"profilePic":1})
        result.append(d)

    if total_count <= offset+limit:
        next_url = None
    else:
        next_url = "getfollowing?limit=" + str(limit+10) +"&offset=" + str(offset)
    if offset != 0:
        previous_url = "getfollowing?limit=" + str(limit-10) +"&offset=" + str(offset)
    else: 
        previous_url = "getfollowing?limit=" + str(limit-10) +"&offset=" + str(offset)
    
    output = {
        "data":result, 
        "total_count": total_count,
        "previous_url":previous_url,
        "next_url":next_url,
        
    }
    return {"status": codes.OK, "result": output, "message": messages.USER_DETAILS_FETCHED}


def getFollowingOthers(db,offset,limit, id, token_uid):
    try:
        doc = db.users.find_one({"_id": ObjectId(id)}, {"UID": 1, "_id": 0})
        UID = doc["UID"]
        stating_id = db.followers.find({"followingID":UID}, {}).sort('_id', -1)
        total_count = stating_id.count()
        last_id = stating_id[offset]["_id"]
        res = db.followers.find({"_id":{"$lte" : last_id },"followingID":UID},{"UID":1,"_id":0}).sort('_id', -1).limit(limit)
    except Exception as e:
        res = []
        total_count = 0
    result = []
    for i in res:
        d = db.users.find_one({"UID":i["UID"]},{"_id":0,"firstName":1,"lastName":1,"UID":1,"profilePic":1})
        doc = db.followers.find_one({"UID":d['UID'] , "followingID":token_uid})
        if doc:
            d['following'] = True
        else:
            d['following'] = False
        result.append(d)

    if total_count <= offset+limit:
        next_url = None
    else:
        next_url = "getfollowingOthers?limit=" + str(limit+10) +"&offset=" + str(offset)
    if offset != 0:
        previous_url = "getfollowingOthers?limit=" + str(limit-10) +"&offset=" + str(offset)
    else: 
        previous_url = "getfollowingOthers?limit=" + str(limit-10) +"&offset=" + str(offset)
    
    output = {
        "data":result, 
        "total_count": total_count,
        "previous_url":previous_url,
        "next_url":next_url,
        
    }
    return {"status": codes.OK, "result": output, "message": messages.USER_DETAILS_FETCHED}



def getFollowers(db,offset,limit,id):
    try:
        doc = db.users.find_one({"_id": ObjectId(id)}, {"UID": 1, "_id": 0})
        UID = doc["UID"]
        stating_id = db.followers.find({"UID":UID}, {}).sort('_id', -1)
        total_count = stating_id.count()
        last_id = stating_id[offset]["_id"]
        res = db.followers.find({"_id":{"$lte" : last_id },"UID": UID}, {"followingID": 1, "_id": 0}).sort('_id', -1).limit(limit)
    except Exception as e:
        res = []
        total_count = 0

    result = []
    for i in res:
        d = db.users.find_one({"UID": i["followingID"]}, {"_id": 0, "firstName": 1, "lastName": 1,"UID":1,"profilePic":1})
        followback = db.followers.find_one({"followingID":UID,"UID":i["followingID"]})

        if followback:
            d['followback'] = False
        else:
            d['followback'] = True
        result.append(d)
    if total_count <= offset+limit:
        next_url = None
    else:
        next_url = "getfollowers?limit=" + str(limit+10) +"&offset=" + str(offset)
    if offset != 0:
        previous_url = "getfollowers?limit=" + str(limit-10) +"&offset=" + str(offset)
    else: 
        previous_url = "getfollowers?limit=" + str(limit-10) +"&offset=" + str(offset)
    output = {
        "data":result, 
        "total_count": total_count,
        "previous_url":previous_url,
        "next_url":next_url,
        
    }
    return {"status": codes.OK, "result": output, "message": messages.USER_DETAILS_FETCHED}


def getFollowersOthers(db,offset,limit, id, token_uid):
    try:
        doc = db.users.find_one({"_id": ObjectId(id)}, {"UID": 1, "_id": 0})
        UID = doc["UID"]
        stating_id = db.followers.find({"UID":UID}, {}).sort('_id', -1)
        total_count = stating_id.count()
        last_id = stating_id[offset]["_id"]
        res = db.followers.find({"_id":{"$lte" : last_id },"UID": UID}, {"followingID": 1, "_id": 0}).sort('_id', -1).limit(limit)
    except Exception as e:
        res = []
        total_count = 0

    result = []
    for i in res:
        d = db.users.find_one({"UID": i["followingID"]}, {"_id": 0, "firstName": 1, "lastName": 1,"UID":1,"profilePic":1})
        doc = db.followers.find_one({"UID":d['UID'] , "followingID":token_uid})
        if doc:
            d['following'] = True
        else:
            d['following'] = False
        if d['UID'] == token_uid:
            d['following'] = None
        result.append(d)
    if total_count <= offset+limit:
        next_url = None
    else:
        next_url = "getfollowersOthers?limit=" + str(limit+10) +"&offset=" + str(offset)
    if offset != 0:
        previous_url = "getfollowersOthers?limit=" + str(limit-10) +"&offset=" + str(offset)
    else: 
        previous_url = "getfollowersOthers?limit=" + str(limit-10) +"&offset=" + str(offset)
    output = {
        "data":result, 
        "total_count": total_count,
        "previous_url":previous_url,
        "next_url":next_url,
        
    }
    return {"status": codes.OK, "result": output, "message": messages.USER_DETAILS_FETCHED}


def getFollowerRequests(db, id):
    doc = db.users.find_one({"_id": ObjectId(id)}, {"UID": 1, "_id": 0})
    UID = doc["UID"]
    res = db.followRequests.find({"UID": UID}, {"followingID": 1, "_id": 0})
    result = []
    for i in res:
        d = db.users.find_one({"UID": i["followingID"]}, {"_id": 0, "firstName": 1, "lastName": 1, "UID": 1})
        result.append(d)
    return {"status": codes.OK, "result": result, "message": messages.USER_DETAILS_FETCHED}


def respondRequest(db,setObj,id):
    UID = db.users.find_one({"_id": ObjectId(id)}, {"UID": 1, "_id": 0})
    UID = UID["UID"]
    res = db.followRequests.find_one({"UID": UID, "followingID":setObj["UID"]}, {"_id": 0})
    if res is not None:
        if setObj["action"] == True:
            doc = db.followers.insert(res)
            doc1 = db.followRequests.remove({"UID":res["UID"],"followingID":res["followingID"]})
            return {"status": codes.OK, "result": "Request Accepted Successfully", "message": messages.REQUEST_ACCEPTED_SUCCESSFULLY}
        elif setObj["action"] == False:
            doc = db.followRequests.remove({"UID":res["UID"],"followingID":res["followingID"]})
            return {"status": codes.OK, "result": "Request Rejected Successfully","message": messages.REQUEST_DECLINED_SUCCESSFULLY}
        return {"status": codes.BAD_REQUEST, "result": "Some Problem Occured","message": messages.SOME_ERROR_OCCURED}
    
    return {"status": codes.BAD_REQUEST, "result": "No Request from Such User Found","message": messages.INVALID_DATA}




def unFollowUser(db,setObj,id):
    doc = db.users.find_one({"_id": ObjectId(id)}, {"UID": 1, "_id": 0})
    UID = doc["UID"]
    doc = db.followers.remove({"UID":setObj["UID"], "followingID":UID})
    if doc["n"] == 1:
        return {"status": codes.OK, "result": "User UnFollowed Successfully", "message": messages.UNFOLLOWED_SUCCESSFULLY}
    else:
        return {"status": codes.OK, "result": "User already not followed","message": messages.UNFOLLOW_UNSUCCESSFULL}



def changeUserPrivacy(db, setObj, id):
    doc = db.users.update({'_id':ObjectId(id)}, {"$set":{"isPrivate":setObj["isPrivate"]}})
    if doc:
        return {"status": codes.OK, "result": "User privacy changed","message": messages.USER_PRIVACY_CHANGED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.PRIVACY_NOT_CHANGED}

def viewOtherProfile(db,setObj,id):
    doc = db.users.find_one({"UID":setObj["UID"]},{"_id":0,"UID":1,"firstName":1,"username":1,"full_name":1,"lastName":1,"aboutMe":1,"interests":1,"country":1,"nickName":1,"email":1,"profilePic":1})
    doc['full_name'] = doc['firstName']+doc['lastName']
    if "aboutMe" not in doc:
        doc["aboutMe"] = ""
        doc["AboutMe"] = ""
    else:
        doc["AboutMe"] = doc["aboutMe"]
    if "interests" not in doc:
        doc["interestedFinancialInstruments"] = ""
    if "profilePic" not in doc:
        doc["profilePic"] = ""
    if "nickName" not in doc:
        doc["nickName"] = ""
    

    UID = db.users.find_one({"_id":ObjectId(id)})['UID']
    if doc:
        doc1 = db.followers.find_one({"UID":setObj['UID'] , "followingID":UID})
        if doc1:
            doc['following'] = True
        else:
            doc['following'] = False
        return {"status": codes.OK, "result": doc,"message": messages.USER_DETAILS_FETCHED}
    else:
        return {"status": codes.BAD_REQUEST, "result": "User does not exist", "message": messages.USER_DOES_NOT_EXIST}


def addAboutMe(db, setObj, id):
    doc = db.users.update({"_id":ObjectId(id)},{"$set":setObj})
    if doc:
        if doc:
            return {"status": codes.OK, "result": "Details added Successfully","message": messages.USER_DEATAILS_ADDED_SUCCESSFULLY}
        else:
            return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED","message": messages.SOME_ERROR_OCCURED}

def getLeaderBoard(db,id,userType, offset, limit, search=None):
    offset = offset
    limit = limit
    if search:
        rgx = re.compile('.*{}.*'.format(search), re.IGNORECASE)
    # stating_id = db.users.find({}, {'password':0}).sort('_id', -1)
    if userType is None:
        try:
            stating_id = db.users.find({}, {'password':0}).sort('_id', -1)
            last_id = stating_id[offset]["_id"]
            if search:
                users = db.users.find({"full_name":rgx,"isCSVUploaded":True,"isActive":True,"_id":{"$lte" : last_id }},{'password':0}).sort('_id', -1).limit(limit)
            else:
                users = db.users.find({"isCSVUploaded":True,"isActive":True,"_id":{"$lte" : last_id }},{'password':0}).sort('_id', -1).limit(limit)
        except Exception as e :
            users = []
            total_count = 0
    elif userType == 'expertTrade':
        try:
            stating_id = db.users.find({"isVerifiedTrader":True}, {'password':0}).sort('_id', -1)
            last_id = stating_id[offset]["_id"]
            if search:
                users = db.users.find({"full_name":rgx,"isCSVUploaded":True,"isActive":True,"_id":{"$lte" : last_id }, "isVerifiedTrader":True},{'password':0}).sort('_id', -1).limit(limit)
            else:
                users = db.users.find({"isCSVUploaded":True,"isActive":True,"_id":{"$lte" : last_id }, "isVerifiedTrader":True},{'password':0}).sort('_id', -1).limit(limit)
            # users = db.users.find({"isVerifiedTrader":True})
        except Exception as e :
            users = []
            total_count = 0
    elif userType == 'mentor':
        try:
            stating_id = db.users.find({"isMentor":True}, {'password':0}).sort('_id', -1)
            last_id = stating_id[offset]["_id"]
            if search:
                users = db.users.find({"full_name":rgx,"isCSVUploaded":True,"isActive":True,"_id":{"$lte" : last_id }, "isMentor":True},{'password':0}).sort('_id', -1).limit(limit)    
            else:
                users = db.users.find({"isCSVUploaded":True,"isActive":True,"_id":{"$lte" : last_id }, "isMentor":True},{'password':0}).sort('_id', -1).limit(limit)
            # users = db.users.find({"isMentor":True})
        except Exception as e :
            users = []
            total_count = 0
        
    check = {}
    result = []
    final_result = []
    total_count = 0
    id = db.users.find_one({"_id": ObjectId(id)}, {"_id": 0, "UID": 1})['UID']
    for user in users:
        print("{} - {} - {}".format(user["_id"], user['isCSVUploaded'], user['isActive']))
        entry_amount = 0
        if (user['isCSVUploaded'] == 'true' or user['isCSVUploaded'] == True) and user['isActive'] == True:
            allTransactions = db.transactions.find({"UID":user["UID"]}).sort('DATE', 1)
            all_data = []
            
            for i in allTransactions:
                if int(float(i["entry_amount"])) == 0:
                    entry_amount = float(i["exit_amount"])

                i["AMOUNT"] = float(i["AMOUNT"])
                i["p&l"] = float(i["p&l"])
                i["balance"] = float(i["balance"])
                i["percentage_changes"] = float(i["percentage_changes"])
                i["entry_amount"] = float(i["entry_amount"])
                i["exit_amount"] = float(i["exit_amount"])
                i["profit"] = float(i["profit"]) if i["profit"] is not None else None
                i["loss"] = float(i["loss"]) if i["loss"] is not None else None
                all_data.append(i)
                # print(i)
            # loc = services.user.fetchFileLoc(db,id)
            # print(pandas.DataFrame(all_data)
            if all_data != []:

                df = pandas.DataFrame(all_data)
                res = calculations.user.getBasicCalc(df)
                res['UID'] = user['UID']
                if 'isMentor' in user:
                    res['isMentor'] = user['isMentor']
                else:
                    res['isMentor'] = False
                if 'isVerifiedTrader' in user:   
                    res['isVerifiedTrader'] = user['isVerifiedTrader']
                else:
                    res['isVerifiedTrader'] = False
                res['country'] = user['country'] if "country" in user else "USA"
                res['countryCode'] = user['countryCode'] if "countryCode" in user else "AQ"
                res['username'] = user['firstName'] + " " + user['lastName']
                if 'profilePic' in user:
                    res['profilePic'] = user['profilePic'] 
                else:
                    res['profilePic'] = None
                doc = db.followers.find_one({"UID":user['UID'] , "followingID":id})
                if doc:
                    res['following'] = True
                else:
                    res['following'] = False

                if id == user['UID']:
                    res['following'] = None
                total_count = total_count + 1
                result.append(res)
                check[user['UID']] = res['balance']
        
    k = Counter(check)

    # Finding 3 highest values
    high = k.most_common(10)
    if len(high) < 10:
        l = len(high)
    else:
        l = 10
    for i in range(l):
        for j in result:
            if j['UID'] == high[i][0]:
                final_result.append(j)


    output={
        "data":final_result,
        "total_count":total_count
    }


    return {"status": codes.OK, "result": output,"message": messages.USER_DEATAILS_ADDED_SUCCESSFULLY}

def max_dradown(balance):
  l = len(balance)
  all_dradowns = []
  max_draw_ammount = []
  res = {}
  for i in range(l-1):
    trough_value = balance[i]
    crest_value = balance[i]
    for j in range(i+1,l):
      pl = balance[j] - balance[i]
      if pl < 0:
        trough_value = balance[j]
      elif pl > 0:
        break
    drawdown = round((trough_value-crest_value)/crest_value * 100,2)
    max_draw_ammount.append(trough_value-crest_value)
    all_dradowns.append(drawdown)
  res['max_drawdown_amount'] = round(abs(min(max_draw_ammount)),2) if max_draw_ammount != [] else 0
  res['max_drawdown_percent'] = str(round(abs(min(all_dradowns)),2))+'%' if all_dradowns != [] else 0 
  return res


def getTransactionByDate(db,id,date,offset,limit,search=None):
    UID = db.users.find_one({"_id": ObjectId(id)}, {"_id": 0})['UID']
    if search:
        rgx = re.compile('.*{}.*'.format(search), re.IGNORECASE)
    stating_id = db.transactions.find({"UID":UID,"DATE":date}).sort('_id', -1)
    last_id = stating_id[offset]["_id"]
    if search:
        allTransactions = db.transactions.find({"SYMBOL":rgx,"UID":UID, "DATE":date,"_id":{"$lte" : last_id }}).limit(limit)
    else:
        allTransactions = db.transactions.find({"UID":UID, "DATE":date,"_id":{"$lte" : last_id }}).limit(limit)
    result = []
    total_count=0
    for transactions in allTransactions:
        transactions["_id"] = str(ObjectId(transactions["_id"]))
        total_count+=1
        result.append(transactions)

    output={
        "data":result,
        "total_count":total_count
    }
    return {"status": codes.OK, "result": output, "message": messages.USER_DEATAILS_ADDED_SUCCESSFULLY}





def becomementorship(db, id):
    UID = db.users.find_one({"_id":ObjectId(id)},{"UID":1,"_id":0})["UID"]
    doc = db.users.update_one({"UID":UID},{"$set":{"mentor_request":1}})
    if doc:
        if doc:
            return {"status": codes.OK, "result": "Successfully become a mentor","message": messages.MENTOR_ADDED_SUCCESSFULLY}
        else:
            return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED","message": messages.SOME_ERROR_OCCURED}


def becomeexpertise(db, id):
    UID = db.users.find_one({"_id":ObjectId(id)},{"UID":1,"_id":0})["UID"]
    doc = db.users.update_one({"UID":UID},{"$set":{"trader_request":1}})
    if doc:
        if doc:
            return {"status": codes.OK, "result": "Successfully become a expert","message": messages.EXPERT_ADDED_SUCCESSFULLY}
        else:
            return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED","message": messages.SOME_ERROR_OCCURED}


def updateTransaction(db,setObj):
    id = setObj["_id"]
    del setObj["_id"]
    doc = db.transactions.update({"_id":ObjectId(id)},{"$set":setObj})
    if doc['n']>0:
        return {"status": codes.OK, "result": "Successfully become a expert","message": messages.TRANSACTION_UPDATED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}



def notice(db, offset, limit, id):
    offset = offset
    limit = limit
    try:
        UID = db.users.find_one({"_id":ObjectId(id)})['UID']
        stating_id = db.notifications.find({"UID":UID}, {}).sort('_id', -1)
        total_count = stating_id.count()
        last_id = stating_id[offset]["_id"]
        res = db.notifications.find({"_id":{"$lte" : last_id }, "UID":UID},{'_id': 0}).sort('_id', -1).limit(limit)
    except Exception as e :
        res = []
        total_count = 0

    result = []
    for i in res:
        result.append(i)
    
    if total_count <= offset+limit:
        next_url = None
    else:
        next_url = "getnotification?limit=" + str(limit+10) +"&offset=" + str(offset)
    if offset != 0:
        previous_url = "getnotification?limit=" + str(limit-10) +"&offset=" + str(offset)
    else: 
        previous_url = "getnotification?limit=" + str(limit-10) +"&offset=" + str(offset)

    output = {
        "data":result, 
        "total_count": total_count,
        "previous_url":previous_url,
        "next_url":next_url,
        
    }
    return {"status": codes.OK, "result": output, "message":messages.NOTIFICATION_FETCH_SUCCESSFULLY}



def csvpathdata(db, id):
    doc = db.users.find_one({"_id":ObjectId(id)})["UID"]
    data = db.transactions.find({"UID":doc}, {"_id":0})
    all_data = []
    for d in data:
        all_data.append(d)    
    # CSVpath = doc['CSV']
    # if CSVpath:
    
    return {"status": codes.OK, "result": all_data ,"message": messages.CSV_UPLOADED_SUCCESSFULLY}
    # else:
    #     return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED","message": messages.SOME_ERROR_OCCURED}

def add_manual_data(db, setObj):
    tran = db.transactions.find({'UID':setObj['UID']}).sort([('_id', -1)]).limit(1)
    for i in tran:
        setObj['balance'] = round(float(i['balance']) + float(setObj['p&l']),2)
        setObj['percentage_changes'] = round(((float(setObj['balance'])-float(i['balance']))/float(i['balance']))*100,2)
    else:
        setObj['balance'] = setObj['p&l']
        setObj['percentage_changes'] = setObj['p&l_percent']
    if 'p&l' in setObj:
        if int(setObj['p&l']) > 0:
            setObj['profit'] = setObj['p&l']
            setObj['win_percentage'] = setObj['p&l_percent']
            setObj['loss_percentage'] = None
            setObj['loss'] = None
        else:
            setObj['profit'] = None
            setObj['win_percentage'] = None
            setObj['loss'] = setObj['p&l']
            setObj['loss_percentage'] = setObj['p&l_percent']
    del setObj['p&l_percent']
    setObj['setup'] = None
    setObj['entryLevel'] = None
    setObj['emotion'] = None
    setObj['DESCRIPTION'] = None
    setObj['PRICE'] = None
    setObj['COMMISSION'] = None
    setObj['AMOUNT'] = round(int(setObj['QUANTITY']) * int(setObj['exit_amount']),2)
    setObj['REG FEE'] = None
    setObj['TRANSACTION ID'] = None
    
    
        
    doc = db.transactions.insert(setObj)
    if doc:
        doc1 = db.users.update_one({"UID":setObj['UID']},{"$set": {"isCSVUploaded": True}})
        return {"status": codes.OK, "result": "Success" ,"message": messages.MANUAL_DATA_ADDED}
    else:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED} 

def get_card_details(db, setObj):
    details = db.card_details.find({"UID":setObj['UID']},{"_id":0})
    if details:
        res = []
        for detail in details:
            detail['CVV'] = '***'
            detail['card_number'] ='**** **** **** ' + detail['card_number'][12:]
            res.append(detail)
        return {"status": codes.OK, "result": res ,"message": messages.DETAIL_FETCHED_SUCCESSFULLY}
    return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}
   


def save_card_details(db, setObj):
    if "card_number" in setObj:
        card_number = setObj['card_number']
        card_number = card_number.replace(" ","")
        setObj['card_number'] = card_number
    valid = validations.user.validateCardDetails(setObj)
    user = db.users.find_one({"UID":setObj['UID']})
    if valid == True:
        doc1 = db.card_details.find_one({'card_number':setObj['card_number'],"UID":setObj["UID"]})
        if doc1 is None:
            check_card  = payments.generate_card_token(setObj['card_number'],setObj['expiry_month'],setObj['expiry_year'],setObj['CVV'])
            if check_card['code'] == "400":
                return {"status": codes.BAD_REQUEST, "result": check_card['message'], "message": check_card['message']}
            else:
                existing_customer = db.stripe_token.find_one({"UID":setObj["UID"]})
                if existing_customer == None:
                    customer_create = payments.Create_customer(check_card['token']['token_id'],user['email'],user['firstName'],user['lastName'])
                    if customer_create['code'] == "200":
                        customer_create  = customer_create['token']
                    else:
                        return {"status": codes.BAD_REQUEST, "result": customer_create['message'], "message": customer_create['message']}
                else:
                    customer_create = existing_customer['customer_id']
                    create_card =  payments.existing_customer(customer_create,check_card['token']['token_id'])
                    if create_card['code'] == "400":
                        return {"status": codes.BAD_REQUEST, "result": create_card['message'], "message": create_card['message']}
               
            result = {}
            result['card_token'] = check_card['token']['card_id']
            result['token_id'] = check_card['token']['token_id']
            result['customer_id'] = customer_create
            result['UID']  = setObj['UID']
            setObj ['card_token']  = check_card['token']['card_id']
            doc = db.stripe_token.insert_one(result) 
            doc2 = db.card_details.find_one({"UID":setObj['UID']})
            if doc2 is None:
                setObj['is_default'] = True
            else:
                setObj['is_default'] = True
            doc = db.card_details.insert_one(setObj)
            if doc:
                return {"status": codes.OK, "result": "Success" ,"message": messages.CARD_DETAILS_SAVED}
            else:
                return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}
        else:
            return {"status": codes.BAD_REQUEST, "result": "Card Number Already Exists", "message": messages.CARD_ALREADY_EXISTS}
    else:
        message = valid[0] + ' is not Valid'
        return {"status": codes.BAD_REQUEST, "result": "Please Enter Valid Data", "message": message}



def delete_card_details(db, setObj):
    card = db.card_details.find_one({'card_number':setObj['card_number'],"UID":setObj["UID"]})
    if card == None:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}
    else:
        card_token = card['card_token']

    customer = db.stripe_token.find_one({"UID":setObj['UID']})
    if customer == None:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED} 
    else:
        customer_token = customer['customer_id']

    remove_card = payments.delete_card(customer_token,card_token)
    if remove_card['code'] == "400":
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": remove_card['message']}
    else:
        doc = db.card_details.remove({"card_number":setObj['card_number'],"UID":setObj['UID']})
        doc1 = db.stripe_token.remove({"card_token":card_token,"customer_id":customer_token,"UID":setObj['UID'],})
        if doc and doc1:
            return {"status": codes.OK, "result": "Success" ,"message": messages.CARD_DELETED_SUCCESSFULLY}
        else:
            return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED} 

def update_default_card(db, setObj):
    card_number = setObj['card_number']
    card_number = card_number.replace(" ","")
    setObj['card_number']  = card_number
    doc1 = db.card_details.update({"UID":setObj['UID']},{"$set":{"is_default":False}})
    doc = db.card_details.update_one({"UID":setObj['UID'],"card_number":setObj["card_number"]},{"$set":{"is_default":True}})
    card = db.card_details.find_one({'card_number':setObj['card_number'],"UID":setObj["UID"]})
    if card == None:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}
    else:
        card_token = card['card_token']
    customer = db.stripe_token.find_one({"UID":setObj['UID']})
    if customer == None:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED} 
    else:
        customer_token = customer['customer_id']
    update_default = payments.set_default_card(customer_token,card_token)
    if update_default['code'] == "400":
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": update_default['message']}
    else:
        if doc:
            return {"status": codes.OK, "result": "Success" ,"message": messages.CARD_UPDATED_SUCCESSFULLY}
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED} 

def save_stripe_token(db, setObj):
    doc = db.stripe_token.insert_one(setObj)
    if doc:
        return {"status": codes.OK, "result": "Success" ,"message": messages.TOKEN_SAVED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}

def get_stripe_token(db, setObj):
    token = db.stripe_token.find({"UID":setObj["UID"]},{"_id":0})
    if token:
        res = []
        for i in token:
            res.append(i)
        return {"status": codes.OK, "result": res ,"message": messages.DETAIL_FETCHED_SUCCESSFULLY}
    return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}

def make_payment(db,setObj):
    customer_id = db.stripe_token.find_one({"UID":setObj['UID']})
    if customer_id == None:
        return {"status": codes.BAD_REQUEST, "result":"No Payment Method Added" ,"message": "No Payment Method Added"} 

    customer_id = customer_id['customer_id']
    amount = setObj['amount']
    description = "Subscription"
    plan_type = setObj["plan_type"]
    payment = payments.create_payment_charge(customer_id,amount,description, plan_type)
    if payment['payment_check'] == True:
        result  = {}
        doc1 = db.users.update_one({"UID":setObj["UID"]},{"$set":{"is_subscribed":True, "subscribed_at":(datetime.datetime.utcnow()).strftime("%d-%m-%Y")}})
        result['transaction_time'] = datetime.datetime.utcnow() 
        result['amount'] = payment['amount']/100
        result['transaction_id'] = payment['transaction_id']
        result['UID'] = setObj['UID']
        doc = db.card_transactions.insert_one(result)
        if doc:
            return {"status": codes.OK, "result": payment['message'] ,"message": payment['message']} 
        else:
            return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}
    else:
        return {"status": codes.BAD_REQUEST, "result": payment['message'] ,"message": payment['message']} 


def get_all_transactions(db, setObj):
    transactions = db.card_transactions.find({"UID":setObj["UID"]},{"_id":0})
    user = db.users.find_one({"UID":setObj["UID"]})
    if transactions:
        res = []
        for transaction in transactions:
            if 'full_name' in user:
                transaction['full_name'] = user["full_name"]
            else:
                transaction['full_name'] = user["firstName"] + ' ' + user["lastName"]
            if 'profilePic' in user:
                transaction['profilePic'] = user["profilePic"]
            else:
                transaction['profilePic'] = None
            transaction["email"] = user["email"]
            transaction["transaction_method"] = 'Card'
            transaction["status"] = "Completed"
            transaction_id = transaction["transaction_id"].split('_')
            if len(transaction_id) > 1:
                transaction["transaction_id"] = transaction_id[1]
            else:
                transaction["transaction_id"] = transaction_id[0]


            

            res.append(transaction)
        return {"status": codes.OK, "result": res ,"message": "OK"}
    return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}

def get_subscription_status(db, setObj):
    user = db.users.find_one({"UID":setObj['UID']})
    res = {}
    if 'is_subscribed' in user:
        res['is_subscribed'] = user['is_subscribed']
    else:
        res['is_subscribed'] = False
    return {"status": codes.OK, "result": res ,"message": "OK"}

def test_api1(db, setObj):
    res = {}
    res['success'] = True
    return {"status": codes.OK, "result": res ,"message": "OK"}

def get_institutions(db,setObj):
    res={}
    if 'country_codes' in setObj and "count" in setObj and "offset" in setObj:
        data ={"client_id": "6124a9928fc32f0010278d45",
        "secret":"4fb68f2fcf2fdf2c3b1f8602421194",
        "count": setObj["count"],
        "offset": setObj["offset"],
        "country_codes":setObj["country_codes"] }

        url="https://sandbox.plaid.com/institutions/get"
        response = requests.post(url, data=json.dumps(data), headers=headers)
        data=response.json()
        data=data["institutions"]
        res["data"]=data

        for inst in data :
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            # print(type(inst))
            inst=dict(inst)
            doc = db.insitution_data.insert_one(inst)

        return {"status": codes.OK, "result": res ,"message": "OK"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}


def update_data(db,setObj):
    res={}
    if 'institutions_id' in setObj and "user_name" in setObj and "password" in setObj:

        return {"status": codes.OK, "result": res ,"message": "data updated successfully!"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message":"Please fill all the required fields"}


def get_symbols(db,setObj):

    transactions = db.transactions.find({"UID":setObj["UID"]})
    if transactions :
        res = {}
        symbols=[]
        for transaction in transactions:
            if 'SYMBOL' in transaction:
                symbols.append(transaction['SYMBOL'])
        
        symbols=set(symbols)
        res["symbols"]=list(symbols)
        return {"status": codes.OK, "result": res ,"message": "OK"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message": messages.SOME_ERROR_OCCURED}

        
def google_pay(db, setObj):

    user = db.users.find_one({"UID":setObj['UID']})
    doc1 = db.users.update_one({"UID":setObj['UID']},{"$set":{"is_subscribed":True}})
    res = {}
    if 'is_subscribed' in user:
        res['is_subscribed'] = user['is_subscribed']
    else:
        res['is_subscribed'] = False
    return {"status": codes.OK, "result": True ,"message": "OK"}


def search_ticker(db, setObj):
    from bson import json_util
    from datetime import datetime
    from datetime import timedelta
    today=datetime.now().date()
    today_day=today.day
    today_month=today.month
    today_year=today.year

    yesterday = datetime.now() - timedelta(days = 1)
    yesterday=yesterday.date()
    yesterday_day=yesterday.day
    yesterday_month=yesterday.month
    yesterday_year=yesterday.year


    res={}
    if "search" in setObj and setObj["search"]!= "":
        search = setObj["search"]
        rgx = re.compile('.*{}.*'.format(search), re.IGNORECASE)
        data = db.ticker.find({"name":rgx})

        data=json.loads(json_util.dumps(data))
        result=[]
        for da in data:
            url = 'https://api.polygon.io/v2/aggs/ticker/{}/range/1/day/{}-{}-{}/{}-{}-{}?apiKey=DvTLBEY0TnOQGIjJHFjmsqQ2ZjM9bLWM'.format(da["ticker"],yesterday_year,yesterday_month,yesterday_day,today_year,today_month,today_day)
            # print("-------------------------------")
            # print(url)
            respone=requests.get(url)

            if 'results' in json.loads(respone.text):

                stock_data=json.loads(respone.text)['results'][0]
                da["market_data"]={
                    'c':stock_data["c"],
                    'h':stock_data["h"],
                    'l':stock_data["l"],
                }
                # print("--------------------------")
                # print(stock_data)
            result.append(da)

        # result2=[]
        # for item in result:
        #     result2.append(item)

        # for item in data:
        res["data"]=result
        
        # print(res)

        # print("99999999999999999999999999999999999999")
        # print(type(data))

        return {"status": codes.OK, "result": res ,"message": "OK"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message":"Please give the search key"}


# def update_data2(db,setObj):
#     res={}
#     if 'institutions_id' in setObj and "user_name" in setObj and "password" in setObj:

#         return {"status": codes.OK, "result": res ,"message": "data updated successfully!"}
#     else:
#         return {"status": codes.BAD_REQUEST, "result": "SOME PROBLEM OCCURED", "message":"Please fill all the required fields"}







    
    
        
        











