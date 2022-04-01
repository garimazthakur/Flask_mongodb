import sys
import time
import langs
from flask import request
from flask.helpers import make_response
from flask.json import jsonify
from bson import ObjectId
from flask_mail import *
import random
import config
from functools import wraps
import datetime
import jwt
from constants import messages, codes
import boto3, botocore
from io import StringIO, BytesIO
from flask import render_template

IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'PNG']
SECRET_KEY = '1qaz2wsx3edc'

secret_access_key= "r2rxKNzUNBzn9KH9XoHtEDcEVAFH13moV+3LjpjX"
access_key_id = "AKIAWBU5UEEJ45RYT3MQ"
bucket_name = "tryndx"
region = "Asia Pacific (Mumbai) ap-south-1"

def printLog(data):
    print("************************", data, "*****" )


def getFormData(request):
    return {key: value[0] for key, value in request.form.to_dict(flat=False).items()}


def getFormImages(request):
    # print(request.files)
    request.files = request.files.to_dict(flat=False)
    if(len(request.files) == 0):
        return ''
    else:
        request.files = {key: value for key, value in request.files.items()}
        files = []
        for file in request.files[list(request.files.keys())[0]]:
            if file.filename.split(".")[-1] in IMAGE_EXTENSIONS:
                files.append(file)
        return files

def saveImage(image, path):
    # print(image[0])
    image= image
    image_name = "-".join((image.filename).split(" "))

    s3 = boto3.client("s3", aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
    acl="public-read"
    url = s3.upload_fileobj(
            image,
            bucket_name,
            image_name,
            ExtraArgs={
                "ACL": acl,
                "ContentType": image.content_type
            }
        )
    # print(url)
    s3_location = "http://{}.s3.ap-south-1.amazonaws.com/".format(bucket_name)
    # print("{}{}".format(s3_location, image_name))
    return "{}{}".format(s3_location, image_name)

# def saveImage(image, path):
#     image.filename = str(time.time())+"."+image.filename.split(".")[-1]
#     savePath = path + image.filename
#     image.save(savePath)
#     return savePath

# def saveCSV(db,CSV, path):
#     UID = db.users.find_one({"_id":ObjectId(id)},{"UID":1,"_id":0})['UID']
#     CSV.filename = str(time.time())+"."+CSV.filename.split(".")[-1]
#     savePath = path + CSV.filename
#     df.to_csv(savePath)
#     return savePath
def saveCSVinS3(db,csv_file, path, id):
    UID = db.users.find_one({"_id": ObjectId(id)} , {"UID":1,"_id":0})['UID']
    filename = str(time.time())+"."+UID.split(".")[-1]
    savePath = filename + '.csv'
    # csv_buffer = StringIO()
    # df.to_csv(csv_buffer)

    # df.to_csv(savePath)
    acl="public-read"
    # return {'CSV': savePath}
    # s3_resource = boto3.resource('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
    # s3_resource.Bucket(bucket_name).Acl().put(ACL='public-read')
    # s3_resource.Object(bucket_name, filename).put(Body=csv_buffer.getvalue())
    
    s3 = boto3.client("s3", aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key)
    # import io
    url = s3.upload_fileobj(
            csv_file,
            bucket_name,
            filename+".csv",
            ExtraArgs={
                "ACL": acl,
                "ContentType": "csv"
            }
        )
    # print(url)
    s3_location = "http://{}.s3.ap-south-1.amazonaws.com/".format(bucket_name)
    return {'CSV': s3_location+filename+".csv"}
    # print(s3_location+filename+".csv")

def saveCSV(db,df, path, id):
    UID = db.users.find_one({"_id": ObjectId(id)} , {"UID":1,"_id":0})['UID']
    filename = str(time.time())+"."+UID.split(".")[-1]
    savePath = path + filename + '.csv'
    df.to_csv(savePath)
    return {'CSV': savePath}


def response(status, data, message, lang="en", token = None):
    if lang == None:
        lang = "en"
        if langs.messages[lang].get(message) == None:
            message = message
        else:
            message = langs.messages[lang].get(message)
    if token:
        #token = token[2:-1]
        return make_response(jsonify({"status": status, "message": message, "result": data, "token":token}), status)
    else:
        return make_response(jsonify({"status": status, "message": message, "result": data}), status)


def response1(status, data, message, lang="en", token = None):
    if lang == None:
        lang = "en"
        if langs.messages[lang].get(message) == None:
            message = message
        else:
            message = langs.messages[lang].get(message)
    if token:
        #token = token[2:-1]
        return make_response(jsonify({"status": status, "message": message, "result": data, "token":token}), status)
    else:
        return make_response(jsonify({"status": status, "message": message, "result": data}), status)





def token_required(f):
    @wraps(f)
    def decorated(*argrs, **kwargs):
        token = request.headers.get('authorization')
        if not token:
            return jsonify({'Message': 'Token is missing'})
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms = 'HS256')
        except:
            return response(codes.BAD_REQUEST, 'Session Expired, Please Login Again.', 'Session Expired, Please Login Again.')
            # return jsonify({'status':400,'message':''})
        return f(*argrs, **kwargs)
    return decorated


def token_required_param(f):
    @wraps(f)
    def decorated(*argrs, **kwargs):
        token = request.args.get('authorization')
        if not token:
            return jsonify({'Message': 'Token is missing'})
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms = 'HS256')
        except:
            return jsonify({'message':'Token is Invalid'})
        return f(*argrs, **kwargs)
    return decorated


def getID(token):
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms = 'HS256')
    # print(">>>>>>>>>>> {}".format(type(decoded_token)))
    return decoded_token

import base64
def generateLink(db,setObj,mail):
    email = setObj['email']
    doc =  db.admin.find_one({"email":email})
    
    new_token = base64.b64encode(email.encode("ascii")).decode("ascii")
    if doc:
        token = random.randint(0,9999)
        msg = Message('Password reset for TryndX', sender='username@gmail.com', recipients=[email])
        msg.body="""<html><body><b>Greeting from TryndX, Please press below button for reset your password: </b> <br> <a href="https://admin.tryndx.com/reset-password?token={}" target="_blank"><button type="button">Click Here</button></a></body></html>""".format(new_token)
        msg.html = msg.body
        mail.send(msg)
        existing = db.resetToken.find_one({"email":email})

        if existing is None:
            ins = db.resetToken.insert({"email":email,"token": new_token, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)})   
        else:
            upd = db.resetToken.update({"email":email},{"$set":{"token": new_token, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)}})
        return {"status": codes.OK, "result": "Mail has been sent to your registered Mail", "message": messages.MAIL_SENT_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST, "result": "Please enter a valid Mail","message": "Email not registered"}

def generateLinkUser(db,setObj,mail):
    email = setObj['email']
    doc =  db.users.find_one({"email":email})
    
    new_token = base64.b64encode(email.encode("ascii")).decode("ascii")
    if doc:
        token = random.randint(1000,9999)
        msg = Message('OTP Verification for TRYNDx', sender='sagarseth@apptunix.com', recipients=[email])
        msg.body="""<html><body><b>Greeting from TryndX, Please enter the below given OTP for verification: </b> <br>{}<br> </body></html>""".format(token,new_token)
        msg.html=render_template("index2.html", otp=token)
        mail.send(msg)
        existing = db.resetToken.find_one({"email":email})

        if existing is None:
            ins = db.resetToken.insert({"email":email,"token": token, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)})   
        else:
            upd = db.resetToken.update({"email":email},{"$set":{"token": token, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)}})
        return {"status": codes.OK, "result": "Mail has been sent to your registered Mail", "message": messages.MAIL_SENT_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST, "result": "Please enter a valid Mail","message": "Email not registered"}


def getSign(a):
  if a > 0:
    return "+"
  else:
    return "-"

def getInterval(diff):
    if 0 <= diff < 10:
        interval = 1
    elif 10 <= diff < 20:
        interval = 2
    elif 20 <= diff < 30:
        interval = 3
    elif 30 <= diff < 40:
        interval = 4
    elif 40 <= diff < 50:
        interval = 5
    elif 50 <= diff < 100:
        interval = 10
    elif 100 <= diff < 200:
        interval = 40
    else:
        interval = 50
    return interval

