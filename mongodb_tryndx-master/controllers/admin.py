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
def admin(db, config,mail):

    BASE_URL = '/admin/'
    admin = Blueprint('admin', 'admin', __name__)

    @admin.route(BASE_URL+'signup', methods=['POST'])
    def signup():
        body = utils.getFormData(request)
        body['profilePic'] = utils.getFormImages(request)
        body['profilePic'] = utils.saveImage(
            body['profilePic'][0], config.IMAGES_PATHS["ADMIN"]["PROFILE_IMAGE"]["ACTUAL"])
        resp = services.admin.Create(db, body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @admin.route(BASE_URL + 'getallprofile', methods=['GET'])
    @token_required
    def getAllUsers():
        resp = services.admin.profile(db)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @admin.route(BASE_URL + 'getallprofilewithpagination', methods=['GET'])
    @token_required
    def getAllUsersWithPagination():
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        # print(request.args["is_active"])
        if "is_active" in  request.args:
            if request.args["is_active"] == "1":
                check = True
            else:
                check = False
        else:
            check = None
        q = request.args["q"] if "q" in request.args else None
        resp = services.admin.get_all_profile_with_pagination(db, offset, limit, q, check)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
        

    @admin.route(BASE_URL + 'getprofilebyid', methods=['POST'])
    @token_required
    def getUser():
        body = request.get_json()
        resp = services.admin.getUserByID(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @admin.route(BASE_URL + 'login', methods=['POST'])
    def login():
        body = request.get_json()
        resp = services.admin.signin(db, body)
        utils.printLog(resp['token'])
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'), str(resp['token']))


    @admin.route(BASE_URL + 'createuser', methods = ['POST'])
    @token_required
    def createuser():
        body = utils.getFormData(request)
        body['profilePic'] = utils.getFormImages(request)
        if body['profilePic'] == '':
            body['profilePic'] = None
        elif body['profilePic'] != None:
            body['profilePic'] = utils.saveImage(
                body['profilePic'][0], config.IMAGES_PATHS["USER"]["PROFILE_IMAGE"]["ACTUAL"])


        resp = services.admin.create_user(db, body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @admin.route(BASE_URL + 'queryListWithPagination', methods=['GET'])
    @token_required
    def queryListWithPagination():
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        q = request.args["q"] if "q" in request.args else None
        resp = services.admin.userQueryWithPagination(db, offset, limit, q)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @admin.route(BASE_URL + 'viewquery', methods=['GET'])
    @token_required
    def viewQuery():
        resp = services.admin.userQuery(db)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @admin.route(BASE_URL + 'viewquery/byid', methods=['POST'])
    @token_required
    def viewQueryByID():
        body = request.get_json()
        resp = services.admin.userQueryByID(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @admin.route(BASE_URL + 'viewquery/updatequery', methods=['PUT'])
    @token_required
    def updateQueryStatus():
        body = request.get_json()
        resp = services.admin.updateQueryStatus(db, body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
        

    @admin.route(BASE_URL + 'viewquery/addcomment', methods=['PUT'])
    @token_required
    def addQueryComment():
        body = request.get_json()
        resp = services.admin.addQueryCommentbyID(db, body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))




    @admin.route(BASE_URL + 'forgotpassword', methods=['POST'])
    def forgotPassword():
        body = request.get_json()
        resp = utils.generateLink(db,body,mail)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
        
    @admin.route(BASE_URL + 'enternewpassword', methods=['POST'])
    def resetPassword():
        # token = request.args.get('token')
        body = request.get_json()
        resp = services.admin.resetPassword(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @admin.route(BASE_URL + 'viewquery/deletequery', methods=['POST'])
    @token_required
    def delQueryByQID():
        body = request.get_json()
        resp = services.admin.delQueryByQID(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @admin.route(BASE_URL + 'Changepassword', methods=['POST'])
    @token_required
    def ChangePassword():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = request.get_json()
        resp = services.admin.Changepasswordbyadmin(db,body,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    #@admin.route(BASE_URL + 'EditUserByAdmin', methods=['POST'])
    #@token_required
    #def edituserbyadmin():
    #    body['profilePic'] = utils.getFormImages(request)
    #    body['profilePic'] = utils.saveImage(
    #        body['profilePic'][0], config.IMAGES_PATHS["USER"]["PROFILE_IMAGE"]["ACTUAL"])
    #    body = utils.getFormData(request)
    #    resp = services.admin.edituser(db,body)
    #    return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))




    @admin.route(BASE_URL + 'EditUserByAdmin', methods=['POST'])
    @token_required
    def edituserbyadmin():
        body = utils.getFormData(request)
        body['profilePic'] = utils.getFormImages(request)
        if body["profilePic"] == '':
            del body["profilePic"]
        else:
            body['profilePic'] = utils.saveImage(body['profilePic'][0], config.IMAGES_PATHS["ADMIN"]["PROFILE_IMAGE"]["ACTUAL"])
        
        resp = services.admin.edituser(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))





    @admin.route(BASE_URL + 'DeleteUserByAdmin', methods=['POST'])
    @token_required
    def deleteuserbyadmin():
        body = request.get_json()
        resp = services.admin.deleteuser(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @admin.route(BASE_URL + 'ChangeStatus', methods=['POST'])
    @token_required
    def changestatusbyadmin():
        body = request.get_json()
        resp = services.admin.statuschanges(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    #@admin.route(BASE_URL + 'getuserprofile', methods=['GET'])
    #@token_required
    #def getuserProfile():
    #    i = utils.getID(request.headers.get('authorization'))
    #    id = i['id']
    #    resp = services.user.getuserProfileInfo(db, id)
    #    return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
    


    


   



    #@admin.route(BASE_URL+'UploadPic', methods=['POST'])
    #@token_required
    #def usersprofilepic():
    #    body = utils.getFormData(request)
    #    body['profilePic'] = utils.getFormImages(request)
    #    body['profilePic'] = utils.saveImage(
    #        body['profilePic'][0], config.IMAGES_PATHS["ADMIN"]["PROFILE_IMAGE"]["ACTUAL"])
    #    resp = services.admin.Create(db, body)
    #    return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @admin.route(BASE_URL + 'ProfileAdmin', methods=['GET'])
    @token_required
    def getProfileByAdmin():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.admin.adminGetProfileInfo(db, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @admin.route(BASE_URL+'updateAdminProfile', methods=['PUT'])
    @token_required
    def updateAdminProfile():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = utils.getFormData(request)
        body['profilePic'] = utils.getFormImages(request)
        if body["profilePic"] == '':
            del body["profilePic"]
        else:
            body['profilePic'] = utils.saveImage(body['profilePic'][0], config.IMAGES_PATHS["ADMIN"]["PROFILE_IMAGE"]["ACTUAL"])
        
        res = services.admin.updateAdmin(db,body, id)
        return res


    
    @admin.route(BASE_URL+'addpolicyaboutus', methods=['POST'])
    @token_required
    def add_privacy_policy():
        body = request.get_json()
        resp = services.admin.createPolicyAboutus(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
        

    @admin.route(BASE_URL+'getpolicyaboutus', methods=['GET'])
    def get_privacy_policy():
        resp = services.admin.getPolicyAboutus(db)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    
    @admin.route(BASE_URL+'updatepolicyaboutus', methods=['PUT'])
    @token_required
    def update_privacy_policy():
        body = request.get_json()
        resp = services.admin.updatePolicyAboutus(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

       





    return admin
