from constants import codes, messages
from bson import json_util, ObjectId
import json
from werkzeug.security import generate_password_hash, check_password_hash
import validations
import schema
import jwt
import datetime
from utils.utils import SECRET_KEY
import re
from services import user




# Function for creating an Admin
def Create(db, setObj):
    validResp = validations.admin.validateAdmin(setObj, schema.admin.schema)
    if validResp == {}:
        isUnique = validations.admin.isUnique(db,setObj)
        if isUnique == True:
            setObj['password'] = generate_password_hash(setObj['password'])
            if 'country_code' not in setObj:
                setObj['country_code'] = None
            doc = db.admin.insert_one(setObj)
            doc = db.admin.find_one({"_id": doc.inserted_id})
            doc['_id'] = str(doc['_id'])
            return {"status": codes.OK, "result": doc, "message": messages.ADMIN_CREATED_SUCCESSFULLY}
        else:
            return {"status": codes.BAD_REQUEST, "result": {}, "message": messages.USER_IS_ALREADY_EXIST}
    else:
        return {"status": codes.BAD_REQUEST, "result": validResp, "message": messages.INVALID_DATA}

# Function for creating a User (this function will be used by ADMIN)
def create_user(db, setObj):
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
            # print(current_id)
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
            setObj['isPasswordSet'] = False
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
            setObj['created_at'] = datetime.datetime.utcnow()
            setObj['is_subscribed'] = False
            if 'country_code' not in setObj:
                setObj['country_code'] = None
            
            doc = db.users.insert_one(setObj)
            doc = db.users.find_one({"_id": doc.inserted_id})



            doc['_id'] = str(doc['_id'])
            return {"status": codes.OK, "result": doc, "message": "User Created Successfully"}
        else:
            message = unique[0] + ' Already Exist' 
            return {"status": codes.BAD_REQUEST, "result": "You are entering data, which already exist", "message": message}
    else:
        return {"status": codes.BAD_REQUEST, "result": validateResp , "message": validateResp}



def profile(db):
    res = db.users.find({},{'_id': 0,'password':0})
    result = []
    for i in res:
        result.append(i)
    return {"status": codes.OK, "result": result, "message":"User Details Fetched"}

def get_all_profile_with_pagination(db, offset, limit, q, check):
    import re
    user = db.users
    search = q
    offset = offset
    limit = limit 
    # print(search)
    # "/{}/".format()
    rgx = re.compile('.*{}.*'.format(search), re.IGNORECASE)
    # for i in user.find({"username":rgx}):
    #     print(">>>>>>>>>")
    #     print(i)
    if search:
        stating_id = user.find({"$or":[{"firstName":rgx},{"email":rgx},{"phone":rgx},{"username":rgx},{"UID":rgx}, {"full_name":rgx}]},{}).sort('_id', -1)
    
    elif check is not None:
        stating_id = user.find({"isActive":check}, {'password':0}).sort('_id', -1)
    else:
        stating_id = user.find({}, {'password':0}).sort('_id', -1)
    
    # print(total_count)
    try: 
        total_count = stating_id.count()
        last_id = stating_id[offset]["_id"]
        # print(last_id)
        if search :
            # res = user.find({"$and":[{"_id":{"$lte" : last_id }}, {"$or":[{"firstName":search},{"email":search},{"phone":search},{"username":search},{"UID":search}]},{"UID":1,"firstName":1,"lastName":1,"email":1,"phone":1,"username":1,"isActive":1, '_id': 0,'password':0}]}).sort('_id', -1).limit(limit)
            
            res = user.find({"$and":[{"_id":{"$lte" : last_id }}, {"$or":[{"firstName":rgx},{"email":rgx},{"phone":rgx},{"username":rgx},{"UID":rgx}, {"full_name":rgx}]}]},{'_id':0, 'password':0}).sort('_id', -1).limit(limit)
            # res = user.find({"$or":[{"firstName":rgx},{"email":rgx},{"phone":rgx},{"username":rgx},{"UID":rgx}, {"full_name":rgx}]},{'_id':0, 'password':0}).sort('_id', -1).limit(limit)
            # print(">>>>>>>>>>>>")
            # print(res)

        elif check is not None:
            res = user.find({"$and":[{"_id":{"$lte" : last_id }}, {"isActive":check}]},{'_id': 0,'password':0}).sort('_id', -1).limit(limit)
        
        else:
            res = user.find({"_id":{"$lte" : last_id }},{'_id': 0,'password':0}).sort('_id', -1).limit(limit)
            
    except Exception as e:
        total_count = 0
        res = []
    result = []

    for i in res:
        if 'is_social' not in i:
            i['is_social'] = False
        if 'social_type' not in i:
            i['social_type'] = None
        result.append(i)
    if total_count <= offset+limit:
        next_url = None
    else:
        next_url = "getallprofilewithpagination?limit=" + str(limit) +"&offset=" + str(offset+limit)
    if offset != 0:
        previous_url = "getallprofilewithpagination?limit=" + str(limit) +"&offset=" + str(offset-limit)
    else: 
        previous_url = None
    output = {
        "data":result,
        "next_url": next_url, 
        "previous_url":previous_url, 
        "total_count": total_count
    }
    # print({"status": codes.OK, "result": result,  "message":"User Details Fetched"})
    return {"status": codes.OK, "result": output, "message":"User Details Fetched"}

def getUserByID(db,setObj):
    key = list(setObj.keys())
    if key[0] == 'search':
        search = setObj['search']
        res = db.users.find({"$or":[{"firstName":search},{"email":search},{"phone":search},{"username":search},{"UID":search}]},
                            {"_id":0,"password":0})
        result = []
        for i in res:
            result.append(i)
        if res:
            return {"status": codes.OK, "result": result, "message" : "User Details Fetched"}
    elif key[0] == 'UID':
        res = db.users.find_one({"UID":setObj["UID"]},{"_id":0, "password":0})
        if res:
            return {"status": codes.OK, "result": res, "message": "User Details Fetched"}
        else:
            return {"status": codes.NO_CONTENT, "result": "There is no such user", "message": "User Does Not Exist"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "Some error occured", "message": messages.SOME_ERROR_OCCURED}


def signin(db, setObj):
    doc = db.admin.find_one({"email": setObj['email']})
    if doc is None:
        return {"status": codes.BAD_REQUEST, "result": 'Please enter correct EMAIL', "message": "Incorrect Email", "token":''}
    else:
        if check_password_hash(doc['password'],setObj['password']) == True:
            token = jwt.encode({'id':str(doc['_id']), 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes = 1440)}, SECRET_KEY, algorithm = 'HS256')
            if type(token) == bytes :
                token = token.decode("ascii")
                # print(">>>>>>>>>>>>>>{}".format(type(token.decode("ascii"))))
            
            doc['_id'] = str(doc['_id'])
            return {"status": codes.OK, "result": doc, "message": "Admin Login Successfully", "token": token}
        else:
            return {"status": codes.BAD_REQUEST, "result": 'Please enter correct password', "message": "Please enter correct password", "token":''}


def userQueryWithPagination(db, offset, limit, q):
    offset = offset
    limit = limit
    search = q
    rgx = re.compile('.*{}.*'.format(search), re.IGNORECASE)
    if search:
        stating_id = db.userQuery.find({"UID":rgx},{}).sort('_id', -1)
    else:
        stating_id = db.userQuery.find({}).sort('_id', -1)
    
    try: 
        total_count = stating_id.count()
        last_id = stating_id[offset]["_id"]
        if search :
            res = stating_id = db.userQuery.find({"UID":rgx},{"_id":0}).sort('_id', -1).limit(limit)
        else:
            res = db.userQuery.find({"_id":{"$lte" : last_id }},{'_id': 0}).sort('_id', -1).limit(limit)
    except Exception as e:
        total_count = 0
        res = []
    result = []

    for i in res:
        # print(i)
        result.append(i)
    if total_count <= offset+limit:
        next_url = None
    else:
        next_url = "queryListWithPagination?limit=" + str(limit) +"&offset=" + str(offset+limit)
    if offset != 0:
        previous_url = "queryListWithPagination?limit=" + str(limit) +"&offset=" + str(offset-limit)
    else: 
        previous_url = None
    output = {
        "data":result,
        "next_url": next_url, 
        "previous_url":previous_url, 
        "total_count": total_count
    }
    return {"status": codes.OK, "result": output, "message":"User Queries Fetched"}

def userQuery(db):
    res = db.userQuery.find({}, {'_id': 0})
    if res:
        result = []
        for i in res:
            result.append(i)
        return {"status": codes.OK, "result": result, "message": "User Queries Fetched"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "There is some Problem", "message": "Some Error Occured"}


def userQueryByID(db,setObj):
    doc = db.userQuery.find({"UID":setObj['UID']},{'_id':0})
    if doc:
        result = []
        for i in doc:
            result.append(i)
        return {"status": codes.OK, "result": result, "message": "User Queries Fetched"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "There is some Problem", "message": "Some Error Occured"}

def updateQueryStatus(db, setObj):
    res = db.userQuery.find_one({"QID":setObj["QID"]},{"Status":1})
    if res["Status"] == "Open":
        doc = db.userQuery.update({"QID":setObj["QID"]},{"$set":{"Status":"Closed"}})
        return {"status": codes.OK, "result": "Query has been Closed", "message": "Query Status Updated"}
    else:
        doc = db.userQuery.update({"QID": setObj["QID"]}, {"$set": {"Status": "Open"}})
        return {"status": codes.OK, "result": "Query has been opened","message": "Query Status Updated"}

def delQueryByQID(db,setObj):
    doc = db.userQuery.remove({"QID":setObj["QID"]})
    if doc:
        return {"status": codes.OK, "result": "Query has been Deleted", "message": "Query Status Updated"}
    else:
        return {"status": codes.OK, "result": "Query not deleted", "message": "Query Status Updated"}


def addQueryCommentbyID(db, setObj):
    #doc = db.userQuery.find_one({"QID":setObj["QID"]},{"Comment":1})
    #doc['Comment'][str(datetime.datetime.now())] = setObj['Comment']
    res = db.userQuery.update({"QID":setObj["QID"]},{"$set":{"Comment":setObj['Comment']}})
    return {"status": codes.OK, "result": setObj['Comment'] ,"message":"Query Status Updated"}

import base64
def resetPassword(db,setObj):
    token = setObj["token"]
    email = (base64.b64decode((token.encode("ascii")))).decode("ascii")
    setObj["email"] = email
    actualToken = db.resetToken.find_one({"email":email},{"_id":0})
    if actualToken:
        if str(token) == str(actualToken['token']):
            if datetime.datetime.utcnow() < actualToken['exp']:
                doc = db.admin.update({"email":setObj['email']},{"$set":{"password": generate_password_hash(setObj['new_password'])}})
                if doc:
                    delete = db.resetToken.remove({"email":setObj['email']})
                    return {"status": codes.OK, "result": "Password has been reset successfully", "message": "Password Has Been Reset Successfully"}
                else:
                    return {"status": codes.BAD_REQUEST, "result": "Password not set","message": "Password Not Set"}
            else:
                return {"status": codes.BAD_REQUEST, "result": "Provided Link is expired", "message": "Provided Link Is Expired"}
        else:
            return {"status": codes.BAD_REQUEST, "result": "Please enter a valid link", "message": "Please Enter a Valid Link"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "Please send a new link, this link maybe expired","message": "Please Send a New Link, This Link Maybe Expired"}



def Changepasswordbyadmin(db,setObj, id):


    OldPassword = db.admin.find_one({'_id':ObjectId(id)}, {'_id':0,'password':1})
    OldPassword = OldPassword['password']
    if check_password_hash(OldPassword, setObj['OldPassword']) == True:
        hashed_password = generate_password_hash(setObj['password'])

        doc = db.admin.update({'_id':ObjectId(id)},{"$set":{"password":hashed_password}})

        if doc:
            return {"status": codes.OK, "result": "password has been updated123", "message": "Password Updated"}
        else:
            return {"status": codes.OK, "result": "passwod has not update", "message": "Password Has Not Update"}
    else:
        return {"status": codes.BAD_REQUEST, "result": "please enter correct old password", "message": "Please Enter Correct Old Password"}


def edituser(db, setObj):
    if "mentor_request" in setObj:
        if int(setObj["mentor_request"]) == 2:
            setObj["isMentor"] = True
    if "trader_request" in setObj:
        if int(setObj["trader_request"]) == 2:
            setObj["isVerifiedTrader"] = True
    doc = db.users.update({"UID": setObj["UID"]}, {"$set":setObj})
    if doc:
        return {"status": codes.OK, "result": "User Edited successfully", "message" : messages.USER_EDITED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST,"result": "User do not edit" ,"message" : messages.USER_DOES_NOT_EDIT}


def deleteuser(db, setObj):
    doc = db.users.remove({"UID":setObj["UID"]})

    if doc:
        doc1 = db.transactions.remove({"UID":setObj['UID']})
        doc2 = db.followers.remove({"UID":setObj['UID']})
        doc3 = db.followers.remove({"followingID":setObj['UID']})
        return {"status": codes.OK, "result": "User deleted successfully", "message" : messages.USER_DELETED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST,"result": "User is not delete" ,"message" : messages.USER_DOES_NOT_DELETE}



def statuschanges(db, setObj):
    doc = db.users.update({"UID":setObj['UID']},{"$set":{"isActive":setObj["isActive"]}})
    print('********************************************')
    print(doc)
    if doc:
        return {"status": codes.OK, "result": "Status changed Successfully", "message" : messages.STATUS_CHANGED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST,"result": "User status not changed" ,"message" : messages.USER_STATUS_DOES_NOT_CHANGED}


#def getuserProfileInfo(db, id):
#    doc = db.users.find_one({"_id":ObjectId(id)},{"_id":0,"password":0})
#    if doc:
#        return {"status": codes.OK, "result": doc,"message": messages.USER_DETAILS_FETCHED}
#    else:
#        return {"status": codes.BAD_REQUEST, "result": 'user does not exist',"message": messages.SOME_ERROR_OCCURED}

def adminGetProfileInfo(db, id):
    doc = db.admin.find_one({"_id":ObjectId(id)}, {"_id":0, "password":0})
    if doc:
        return {"status": codes.OK, "result": doc,"message": messages.ADMIN_DETAILS_FETCHED}
    else:
        return {"status": codes.BAD_REQUEST, "result": 'admin does not exist',"message": messages.SOME_ERROR_OCCURED}


def updateAdmin(db, setObj, id):

    setObj, bank_data = user.get_bank_data(setObj)
    if "firstName" in setObj and "lastName" in setObj:
        setObj['full_name'] = setObj["firstName"] + " " + setObj["lastName"]
    
    if len(setObj) != 0:
        doc = db.users.update({"_id": ObjectId(id)}, {"$set":setObj})
    if len(bank_data) != 0:
        UID = str(ObjectId(id))
        bank_data["UID"] = UID
        existing_bank_detail = db.bankDetailsAdmin.find_one({"UID":UID})
        print('------------->>')
        # print(existing_bank_detail.count())
        if existing_bank_detail is not None:
            doc1 = db.bankDetailsAdmin.update({"UID":UID},{"$set":bank_data})
        else:
            doc1 = db.bankDetailsAdmin.insert(bank_data)


    doc = db.admin.update({"_id": ObjectId(id)}, {"$set":setObj})
    if doc:
        return {"status": codes.OK, "result": "Admin updated successfully", "message" : messages.ADMIN_UPDATED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST,"result": "There was some problem while updating user information" ,"message" : messages.ADMIN_DOES_NOT_EXIST}
        


def createPolicyAboutus(db,setObj):
    docc = db.policy_aboutus.find_one()
    if not docc:
        doc = db.policy_aboutus.insert(setObj)

        if doc:
            return {"status": codes.OK, "result": "Deatils Added Successfully", "message" : messages.DETAILS_ADDED_SUCCESSFULLY}
        else:
            return {"status": codes.BAD_REQUEST,"result": "There was some problem while updating user information" ,"message" : messages.DETAILS_NOT_ADDED}
    else:
        return {"status": codes.BAD_REQUEST,"result": "Privacy Policy or aboutus is already Added" ,"message" : messages.DETAILS_NOT_ADDED}
def getPolicyAboutus(db):
    doc = db.policy_aboutus.find_one({},{"_id":0})
    if doc:
        return {"status": codes.OK, "result": doc, "message" : messages.DETAIL_FETCHED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST,"result": "There was some problem while updating user information" ,"message" : messages.DETAILS_NOT_FETCHED}


def updatePolicyAboutus(db,setObj):
    id = db.policy_aboutus.find_one()
    if id is None:
        doc = db.policy_aboutus.insert(setObj)
    else:
        id = id["_id"]
        doc = db.policy_aboutus.update({"_id":ObjectId(id)},setObj)
    if doc:
        return {"status": codes.OK, "result": doc, "message" : messages.DETAILS_UPDATED_SUCCESSFULLY}
    else:
        return {"status": codes.BAD_REQUEST,"result": "There was some problem while updating user information" ,"message" : messages.DETAILS_NOT_UPDATED}





