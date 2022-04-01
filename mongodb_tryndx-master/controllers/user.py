from flask import Blueprint, request, make_response, jsonify
from utils import utils
import services
import pandas
import calculations
import random
import datetime
import json
from constants import codes
from bson import ObjectId
import validations
import schema
import numpy



required_headers = ['DATE','TRANSACTION ID','DESCRIPTION','QUANTITY','SYMBOL',
                    'PRICE','COMMISSION','AMOUNT','REG FEE','SHORT-TERM RDM FEE',
                    'FUND REDEMPTION FEE',' DEFERRED SALES CHARGE','T/D','CCY','Tickets',
                    'Shr.Buy','Shr.Sell','Buy Value','Sell Value','Gross P/L','Comm',
                    'SEC','TAF','NSCC','Nasdaq','Net P/L','Net Cash', 'Equity Diff']

mandatory_headers = ["amount"]


def user(db, config, mail):
    BASE_URL = '/user/'
    user = Blueprint('user', 'user', __name__)

    @user.route(BASE_URL+'signup', methods=['POST'])
    def signup():
        body = request.get_json()
        resp = services.user.signup(db, body, mail)
        return utils.response1(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
    
    @user.route(BASE_URL+'verify_otp', methods=['POST'])
    def verify_otp():
        body = request.get_json()
        resp = services.user.verifyOTP(db, body)
        return utils.response1(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL+'login', methods=['POST'])
    def login():
        body = request.get_json()
        resp = services.user.signin(db, body)
        return utils.response1(resp["status"], resp["result"], resp["message"], request.headers.get('lang'), resp["token"])

    @user.route(BASE_URL+'forgot_password', methods=['POST'])
    def forgot_password():
        body = request.get_json()
        resp = services.user.forgotPassword(db,body, mail)
        return utils.response1(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL+'authenticate_otp', methods=['POST'])
    def authenticate_otp():
        body = request.get_json()
        resp = services.user.authenticate_otp(db, body)
        return utils.response1(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
    

    @user.route(BASE_URL+'change_pass_after_otp', methods=['POST'])
    def change_pass_after_otp():
        body = request.get_json()
        resp = services.user.change_pass_after_otp(db, body)
        return utils.response1(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
    
    
    @user.route(BASE_URL + 'social_login', methods = ['POST'])
    def sign_up_social_login():
        body = request.get_json()
        resp = services.user.social_signup(db, body)
        
        return utils.response1(resp["status"], resp["result"], resp["message"], request.headers.get('lang'), resp["token"])

    @user.route(BASE_URL + 'check_user', methods = ['GET'])
    @utils.token_required
    def check_user():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.check_user(db,id)

        return utils.response1(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL+'details', methods=['POST'])
    @utils.token_required
    def details():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = utils.getFormData(request)
        body['profilePic'] = utils.getFormImages(request)
        if body['profilePic'] == '':
            del body['profilePic']
        
        elif body['profilePic'] == []:
            return utils.response(codes.BAD_REQUEST, "Image you are trying to upload is not supported", "This format of image is not acceptable, Accepted Formats are : JPEG, JPG and PNG", request.headers.get('lang'))

        else:
            body['profilePic'] = utils.saveImage(
                body['profilePic'][0], config.IMAGES_PATHS["USER"]["PROFILE_IMAGE"]["ACTUAL"])
        
        resp = services.user.fillDetails(db, body, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @user.route(BASE_URL+'verifymail', methods = ['POST'])
    @utils.token_required
    def sendOTP():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = utils.getFormData(request)
        resp = services.user.generateOTP(body,mail,db,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL + 'verifyotp', methods=['POST'])
    @utils.token_required
    def checkOTP():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = utils.getFormData(request)
        resp = services.user.verify_OTP(db,body,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @user.route(BASE_URL+'resetpassword', methods=['POST'])
    @utils.token_required
    def reset():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = request.get_json()
        resp = services.user.resetPass(db, body, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    # @user.route(BASE_URL+'uploadcsv', methods = ['POST'])
    # @utils.token_required
    # def uploadData():
    #     i = utils.getID(request.headers.get('authorization'))
    #     id = i['id']
    #     csv_file = request.files['csv']
    #     body = {}
    #     # print(config.CSV_PATHS(["USER"]))
    #     body['CSV'] = utils.saveCSV(db, csv_file, config.CSV_PATHS["USER"]["CSV"]["ACTUAL"])
    #     resp = services.user.uploadCSV(db, body, id)
    #     return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL+'uploadData', methods = ['POST'])
    @utils.token_required
    def uploadData():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        csv_file = request.files['csv']
        extension = csv_file.filename.split(".")[-1]
        if extension != 'csv':
            df = pandas.read_excel(csv_file)
            filename = config.temporary["USER"]["ACTUAL"] +  str(random.randint(100000,999999)) + '.csv'
            df.to_csv(filename,index = None,header=True)
            csv_file = open(filename)
        body = {}
        df = pandas.read_csv(csv_file)
        headers = calculations.user.find_headers(df)
        p_l = False
        for i in headers:
            if i not in required_headers:
                df.drop([i], axis = 1, inplace=True)
            if i.lower() in mandatory_headers:
                mandatory_headers.remove(i.lower())
        # mandatory_headers = []
        if mandatory_headers == []:
            body = utils.saveCSVinS3(db,csv_file, config.CSV_PATHS["USER"]["CSV"]["ACTUAL"],id)
            # df = pandas.read_csv(csv_file)
            s = services.user.savecsvInDB(db,df,id)
            resp = services.user.uploadCSV(db, body, id)
            return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
        else:
            return utils.response(codes.BAD_REQUEST, 'Please Enter Appropriate Data', 'Some Mandatory Fields are missing', request.headers.get('lang'))



    @user.route(BASE_URL+'updateprofile', methods=['PUT'])
    @utils.token_required
    def updateuserprofile():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = utils.getFormData(request)
        body['profilePic'] = utils.getFormImages(request)
        if body["profilePic"] == '':
            del body["profilePic"]
        elif body['profilePic'] == []:
            return utils.response(codes.BAD_REQUEST, "Image you are trying to upload is not supported", "This format of image is not acceptable, Accepted Formats are : JPEG, JPG and PNG", request.headers.get('lang'))

        else:
            body['profilePic'] = utils.saveImage(body['profilePic'][0], config.IMAGES_PATHS["USER"]["PROFILE_IMAGE"]["ACTUAL"])
        res = services.user.update(db,body, id)
        return res



    @user.route(BASE_URL + 'userprofile', methods=['GET'])
    @utils.token_required
    def getProfile():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.getProfileInfo(db, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))






    @user.route(BASE_URL + 'dashboard', methods=['POST'])
    @utils.token_required
    def fetchCalc():
        body = request.get_json()
        if body:
            UID = body['UID']
            id = db.users.find_one({"UID":UID})['_id']
            allTransactions = db.transactions.find({"UID":UID}).sort('DATE', 1)
        else:
            i = utils.getID(request.headers.get('authorization'))
            id = i['id']
            UID = db.users.find_one({"_id": ObjectId(id)}, {"_id": 0})['UID']

            allTransactions = db.transactions.find({"UID":UID}).sort('DATE', 1)


        if allTransactions.count() < 5:
            # return "success"
            return utils.response(codes.OK, "None","Please Enter Atleast 5 Trades to use this feature.", request.headers.get('lang'))
            # return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
        entry_amount = 0
        # print(id)
        
        all_data = []

        for i in allTransactions:
            # try:
            if i["entry_amount"] == 'nan':
                i["entry_amount"] = 0
            if int(float(i["entry_amount"])) == 0:
                entry_amount = float(i["exit_amount"])
            
            # except:
            #     entry_amount = 0
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
        # print(pandas.DataFrame(all_data))
        df = pandas.DataFrame(all_data)
        # percentage_change=[]
        # balance = []
        # p_l = []
        # ammount = 0
        # df = df.iloc[::-1]
        # count = 0
        # for i in df["AMOUNT"]:
        #     ammount = ammount+float(i)
        #     if count != 0:
        #         balance.append(ammount)
        #         p_l.append(i)
        #         percentage_change.append(round((p_l[count]/balance[count-1])*100, 2))
        #     else:
        #         balance.append(i)
        #         p_l.append(0.0)
        #         percentage_change.append(0)
        #         entry_amount = i
        #     count = count+1
        # df["p&l"] = p_l
        # df["balance"]=balance
        # df["percentage_changes"]=percentage_change
        if df.empty:
            resp = calculations.user.emptyDF()
            return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))
        headers = calculations.user.find_headers(df)
        resp = calculations.user.overall_performance(df, entry_amount)
        df_cummulative_pnl = calculations.user.calc_cummulative_pnl(df)
        resp['result']['top_bottom_stock'] = df_cummulative_pnl
        startDatePerfomance = request.args.get('startDatePerformance')
        endDatePerfomance = request.args.get('endDatePerformance')
        perfomance_curve = calculations.user.monthwise_balance(entry_amount, df, headers,startDatePerfomance,endDatePerfomance)
        resp['result']['weeklyPerformanceCurve'] = calculations.user.weeklyPerformanceCurve(df,21)
        risk_calc = calculations.user.calc_risk(entry_amount,df)
        resp['result']['performance_curve'] = perfomance_curve
        startDate = request.args.get('startDate')
        endDate = request.args.get('endDate')
                                                                                        
        if startDate:
            startDate = str(startDate)[:10]
            if endDate:
                endDate = str(endDate)[:10]
        if startDate == None and endDate == None:
            startDate =  "2018-01-01"
            # endDate = "2018-05-01"
            endDate = str(datetime.datetime.now())[:10]
        resp['result']['trading_calander'] = calculations.user.tradingCalander(startDate,endDate,df)
        #resp['result']['transactionsByDate'] = calculations.user.transactionsByDate(df,'2018-11-10')
        resp['result']['risk_calc'] = risk_calc
        resp['result']['overall_performance_last30Day'] = calculations.user.overall_performance(df, entry_amount, 30)
        resp['result']['draw_down_streaks'] = calculations.user.draw_down(df)
        resp['result']['tradeSetupAnalytics'] = calculations.user.tradeSetup(db,id)
        resp['result']['tradeEvaluation'] = calculations.user.tradeEvaluation(db,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL + 'filequery', methods=['POST'])
    @utils.token_required
    def fileQuery():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = request.get_json()
        resp = services.user.file_query(db,body,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @user.route(BASE_URL + 'follow', methods=['POST'])
    @utils.token_required
    def follow():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = request.get_json()
        resp = services.user.follow(db,body,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @user.route(BASE_URL + 'getfollowing', methods=['POST'])
    @utils.token_required
    def getFollowing():
        body = request.get_json()
        if body:
            id = db.users.find_one({"UID":body["UID"]})["_id"]
        else:
            i = utils.getID(request.headers.get('authorization'))
            id = i['id']
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        resp = services.user.getFollowing(db,offset,limit, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL + 'getfollowingOthers', methods=['POST'])
    @utils.token_required
    def getFollowingOthers():
        body = request.get_json()
        id = db.users.find_one({"UID":body["UID"]})["_id"]
        
        i = utils.getID(request.headers.get('authorization'))['id']
        token_uid = db.users.find_one({"_id":ObjectId(i)})['UID']
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        resp = services.user.getFollowingOthers(db,offset,limit, id, token_uid)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL + 'getfollowers', methods=['POST'])
    @utils.token_required
    def getFollowers():
        body = request.get_json()
        if body:
            id = db.users.find_one({"UID":body["UID"]})["_id"]
        else:
            i = utils.getID(request.headers.get('authorization'))
            id = i['id']
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        resp = services.user.getFollowers(db,offset,limit, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL + 'getfollowersOthers', methods=['POST'])
    @utils.token_required
    def getFollowersOthers():
        body = request.get_json()
        id = db.users.find_one({"UID":body["UID"]})["_id"]
        
        i = utils.getID(request.headers.get('authorization'))['id']
        token_uid = db.users.find_one({"_id":ObjectId(i)})['UID']
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        resp = services.user.getFollowersOthers(db,offset,limit, id, token_uid)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    



    @user.route(BASE_URL + 'getfollowrequests', methods=['GET'])
    @utils.token_required
    def getFollowRequests():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.getFollowerRequests(db, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL + 'respondrequest', methods=['POST'])
    @utils.token_required
    def respondRequest():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = request.get_json()
        resp = services.user.respondRequest(db,body,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @user.route(BASE_URL + 'unfollow', methods=['POST'])
    @utils.token_required
    def unFollow():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = request.get_json()
        resp = services.user.unFollowUser(db,body,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @user.route(BASE_URL + 'changeprivacy', methods=['POST'])
    @utils.token_required
    def changePrivacy():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = request.get_json()
        resp = services.user.changeUserPrivacy(db, body, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL + 'addaboutme', methods=['POST'])
    @utils.token_required
    def addAboutMe():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        body = request.get_json()
        resp = services.user.addAboutMe(db, body, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL + 'otheruser', methods=['POST'])
    @utils.token_required
    def otherProfile():
        body = request.get_json()
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.viewOtherProfile(db,body,id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @user.route(BASE_URL + 'test', methods=['GET'])
    def test():
        return "Success"





    @user.route(BASE_URL+'viewcsv', methods = ['GET'])
    @utils.token_required
    def viewCSV():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        loc = services.user.fetchFileLoc(db, id)
        
        df = pandas.read_csv(loc)
        return 'success'

    @user.route(BASE_URL + 'leaderboard', methods=['GET'])
    @utils.token_required
    def leaderBoard():
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        userType = request.args.get("userType")
        search = request.args.get("search")
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.getLeaderBoard(db,id,userType, offset, limit, search)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL + 'viewtransactionbydate', methods=['POST'])
    @utils.token_required
    def viewtransaction():
        i = utils.getID(request.headers.get('authorization'))
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        search = request.args.get("search")
        id = i['id']
        body = request.get_json()
        date = body['date']
        resp = services.user.getTransactionByDate(db,id,date,offset, limit, search)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL + 'updatetransaction', methods=['POST'])
    @utils.token_required
    def updatetransaction():
        body = request.get_json()
        resp = services.user.updateTransaction(db,body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))




    @user.route(BASE_URL + 'BecomeMentor', methods=['GET'])
    @utils.token_required
    def userbecomementor():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.becomementorship(db, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL + 'BecomeExpertTrader', methods=['GET'])
    @utils.token_required
    def userbecomeexperttrader():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.becomeexpertise(db, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    

    @user.route(BASE_URL + 'testt', methods=['GET'])
    def testt():
        doc = db.transactions.drop()
        return 'Success'



    @user.route(BASE_URL + 'getnotification', methods=['GET'])
    @utils.token_required
    def notification():
        offset = int(request.args["offset"])
        limit = int(request.args["limit"])
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.notice(db, offset, limit, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    @user.route(BASE_URL + 'getCSV', methods=['GET'])
    @utils.token_required
    def csvpath():
        i = utils.getID(request.headers.get('authorization'))
        id = i['id']
        resp = services.user.csvpathdata(db, id)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))


    @user.route(BASE_URL + 'add_manual_data', methods=['POST'])
    @utils.token_required
    def add_manual_data():
        body = request.get_json()
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.add_manual_data(db, body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL + 'get-card-details', methods=['GET'])
    @utils.token_required
    def get_card_details():
        body = {}
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.get_card_details(db, body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    

    @user.route(BASE_URL + 'save-card-details', methods=['POST'])
    @utils.token_required
    def save_card_details():
        body = request.get_json()
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.save_card_details(db, body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL + 'delete-card-details', methods=['DELETE'])
    @utils.token_required
    def delete_card_details():
        body = request.get_json()
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.delete_card_details(db, body)
        return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))

    @user.route(BASE_URL + 'update-default-card', methods=['PUT'])
    @utils.token_required
    def update_default_card():
        body = request.get_json()
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.update_default_card(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))

    @user.route(BASE_URL + 'save-stripe-token', methods=['POST'])
    @utils.token_required
    def save_stripe_token():
        body = request.get_json()
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.save_stripe_token(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))

    @user.route(BASE_URL + 'get-stripe-token', methods=['GET'])
    @utils.token_required
    def get_stripe_token():
        body = {}
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.get_stripe_token(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))


    @user.route(BASE_URL + 'make-payment', methods=['POST'])
    @utils.token_required
    def make_payment():
        body = request.get_json()
        if "amount" in body:
            i = utils.getID(request.headers.get('authorization'))['id']
            UID = db.users.find_one({"_id":ObjectId(i)})['UID']
            body['UID'] = UID
            resp = services.user.make_payment(db, body)
            return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))
        else:
            return {"message":"Please Fill amount","code":"400"}

    @user.route(BASE_URL + 'get-all-transactions', methods=['GET'])
    @utils.token_required
    def get_transactions():
        body = {}
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.get_all_transactions(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))

    
    @user.route(BASE_URL + 'get-subscription-status', methods=['GET'])
    @utils.token_required
    def get_subscription_status():
        body = {}
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.get_subscription_status(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))

    
    @user.route(BASE_URL + 'test-api', methods=['GET'])
    @utils.token_required
    def test_api():
        body = {}
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.test_api1(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))

        


    @user.route(BASE_URL + 'get-institutions', methods=['POST'])
    def get_institutions():
        body = request.get_json()
        resp = services.user.get_institutions(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))

    

    @user.route(BASE_URL + 'update-data-by-id', methods=['PUT'])
    def update_data():
        body = request.get_json()
        resp = services.user.update_data(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))


    @user.route(BASE_URL + 'get-symbols', methods=['GET'])
    @utils.token_required
    def get_symbols():
        body = {}
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.get_symbols(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))

    @user.route(BASE_URL + 'search-ticker', methods=['POST'])
    def search_ticker():
        body = request.get_json()
        resp = services.user.search_ticker(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))


    @user.route(BASE_URL + 'google-pay', methods=['POST'])
    @utils.token_required
    def google_pay_details():
        body = request.get_json()
        i = utils.getID(request.headers.get('authorization'))['id']
        UID = db.users.find_one({"_id":ObjectId(i)})['UID']
        body['UID'] = UID
        resp = services.user.google_pay(db, body)
        return utils.response(resp['status'],resp['result'],resp['message'],request.headers.get('lang'))
    
















        









        


    

        







    


    
    


        

    # @user.route(BASE_URL+'uploadData', methods = ['POST'])
    # @utils.token_required
    # def uploadDatatest():
    #     i = utils.getID(request.headers.get('authorization'))
    #     id = i['id']
    #     csv_file = request.files['csv']
    #     body = {}
    #     df = pandas.read.csv(csv_file)
    #     headers = calculations.user.find_headers(df)
    #     for i in headers:
    #         if i not in required_headers:
    #             df.drop([i], axis = 1, inplace=True)
    #         #print('**************************')
    #         #print(df)
    #         #filename = datetime.datetime.now()
    #         #df.to_csv('csv_file.csv')
    #     body['CSV'] = utils.saveCSV(df, config.CSV_PATHS["USER"]["CSV"]["ACTUAL"])
    #     resp = services.user.uploadCSV(db, body, id)
    #     return utils.response(resp["status"], resp["result"], resp["message"], request.headers.get('lang'))



    # @user.route(BASE_URL+'viewcsv', methods = ['GET'])
    # @utils.token_required
    # def viewCSV():
    #     i = utils.getID(request.headers.get('authorization'))
    #     id = i['id']
    #     loc = services.user.fetchFileLoc(db, id)
    #     #print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    #     #print(loc)
    #     df = pandas.read_csv(loc)
    #     #print('*******************************')
    #     print(df)
    #     return 'success'


    


        




    return user


