from itertools import count

import numpy as np
from constants import *
from validations import helperFunctions
from utils import *
import math
import services
from datetime import timedelta, datetime
import json
from bson import ObjectId


def calc_cummulative_pnl(df):
    dim = df.shape
    data = {}
    res = {}
    top_3 = []
    bottom_3 = []
    cummulative_pl = np.zeros((26, 1), dtype="int64")
    nan_value = float("NaN")
    d_new = df.groupby(['SYMBOL']).agg({'p&l': 'sum'}).reset_index()
    d_new.replace("", nan_value, inplace=True)
    d_new.dropna(subset = ["SYMBOL"], inplace=True)
    t3 = d_new.nlargest(3, ['p&l']).reset_index()
    b3= d_new.nsmallest(3, ['p&l']).reset_index()
    count = 1
    tp_3 = {}
    top_count = 1
    bottom_count=1
    for sym in t3["index"]:
        data = {
            "Stock Name":t3.loc[t3['index'] == sym, 'SYMBOL'].iloc[0],
            "Cumulative P&L": round(t3.loc[t3['index'] == sym, 'p&l'].iloc[0],2)
        }
        top_3.append(data)
        top_count = top_count+1
        count+=1
    for sym in b3["SYMBOL"]:
        data = {
            "Stock Name":sym,
            "Cumulative P&L": round(b3.loc[b3['SYMBOL'] == sym, 'p&l'].iloc[0],2)
        }
        bottom_3.append(data)
        bottom_count+=1
    res["TOP 3"] = top_3
    res["BOTTOM 3"] = bottom_3
    return res


def performance_per_period(df):
    last3Month = []
    last6Month = []
    lastYear = []
    allTime = []
    lastMonth = []
    res = {}
    df['DATE'] = df['DATE'].astype('datetime64[ns]')
    #for all time
    result = getBasicCalc(df)
    allTime.append(round(result['total_gain']-result['total_loss'], 2))
    allTime.append(round(((result['total_gain']-result['total_loss'])/result['total_gain'])*100, 2))
    
    res['allTime'] = allTime
    #for this year
    currentYear = datetime.now().year
    df['year_number'] = df["DATE"].dt.year
    df_year_wise = df.loc[df['year_number'] == currentYear]
    if df_year_wise.empty:
        lastYear.append(0)
        lastYear.append(0)
        res['LastYear'] = lastYear
    else:
        result = getBasicCalc(df_year_wise)
        lastYear.append(result['total_gain'] - result['total_loss'])
        lastYear.append(round(((result['total_gain'] - result['total_loss']) / result['total_gain']) * 100, 5))
        res['LastYear'] = lastYear
    currentMonth = datetime.now().month
    df['month_number'] = df['DATE'].dt.month
    df_last_month = df.loc[(df['year_number'] == currentYear) & (df['month_number'] == currentMonth)]
    if df_last_month.empty:
        lastMonth.append(0)
        lastMonth.append(0)
        res['lastMonth'] = lastMonth
    else:
        result = getBasicCalc(df_last_month)
        lastMonth.append(result['total_gain'] - result['total_loss'])
        if result['total_gain'] != 0:
            lastMonth.append(round(((result['total_gain'] - result['total_loss']) / result['total_gain']) * 100, 5))
        else:
            lastMonth.append(round(((result['total_gain'] - result['total_loss']) / 1) * 100, 5))
        res['lastMonth']  = lastMonth

    threeMonths = []
    for i in range(6):
        if currentMonth == 0:
            currentMonth = 12
            currentYear -= 1
        threeMonths.append((currentMonth,currentYear))
        currentMonth-=1
    df_last3_month = df.loc[((df['year_number'] == threeMonths[0][1]) & (df['month_number'] == threeMonths[0][0])) |
                            ((df['year_number'] == threeMonths[1][1]) & (df['month_number'] == threeMonths[1][0])) |
                            ((df['year_number'] == threeMonths[2][1]) & (df['month_number'] == threeMonths[2][0]))
                            ]
    if df_last3_month.empty:
        last3Month.append(0)
        last3Month.append(0)
        res['LastThreeMonth'] = last3Month
    else:
        result = getBasicCalc(df_last3_month)
        last3Month.append(result['total_gain'] - result['total_loss'])
        last3Month.append(round(((result['total_gain'] - result['total_loss']) / result['total_gain']) * 100, 5))
        res['LastThreeMonth']   = last3Month

    df_last6_month = df.loc[((df['year_number'] == threeMonths[0][1]) & (df['month_number'] == threeMonths[0][0])) |
                            ((df['year_number'] == threeMonths[1][1]) & (df['month_number'] == threeMonths[1][0])) |
                            ((df['year_number'] == threeMonths[2][1]) & (df['month_number'] == threeMonths[2][0])) |
                            ((df['year_number'] == threeMonths[3][1]) & (df['month_number'] == threeMonths[3][0])) |
                            ((df['year_number'] == threeMonths[4][1]) & (df['month_number'] == threeMonths[4][0])) |
                            ((df['year_number'] == threeMonths[5][1]) & (df['month_number'] == threeMonths[5][0]))
                            ]

    if df_last3_month.empty:
        last6Month.append(0)
        last6Month.append(0)
        res['LastSixMonth'] = last6Month
    else:
        result = getBasicCalc(df_last6_month)
        last6Month.append(result['total_gain'] - result['total_loss'])
        last6Month.append(round(((result['total_gain'] - result['total_loss']) / result['total_gain']) * 100, 5))
        res['LastSixMonth']   = last6Month

    return res







def monthwise_balance(balance,df,headers,startDatePerfomance,endDatePerfomance):
    breaking_points = {}
    dim = (df.to_numpy()).shape
    balance_np_array = []
    balance_np = np.zeros((dim[0], dim[1]-1), dtype = "int64")
    balance_percent = np.zeros((dim[0], dim[1]-1), dtype = "float")
    balance_percent_array = []
    df.drop(df[df["DATE"] == "***END OF FILE***"].index, inplace=True)
    
    df['DATE'] = df['DATE'].astype('datetime64[ns]')
    if startDatePerfomance == None and endDatePerfomance == None:
        startDatePerfomance = '2012-12-31'
        endDatePerfomance = '2021-12-31'
    else:
        startDatePerfomance = startDatePerfomance[:10]
        endDatePerfomance = endDatePerfomance[:10]
    startDatePerfomance = datetime.strptime(startDatePerfomance,"%Y-%m-%d")
    endDatePerfomance = datetime.strptime(endDatePerfomance, "%Y-%m-%d")
    dfDate = df.loc[(df['DATE'] >= startDatePerfomance) & (df['DATE'] <= endDatePerfomance)]
    for date in dfDate["DATE"]:
        balance = df.loc[df['DATE'] == date, 'balance'].iloc[0]
        breaking_points[str(date)[:10]]= round(balance,2)
    mini = -40
    maxi = 40
    diff = int(maxi-mini)
    interval = 5
    profit_loss_distribution = {}
    profit_loss_distribution_last_20 = {}
    a = math.floor(mini)
    b = math.ceil(a + interval)
    #Calculating profit/Loss distribution
    c = helperFunctions.count_range_in_list(list(df["percentage_changes"]),-1000,-40)
    k = "Greater than -40%"
    profit_loss_distribution[k] = c
    for r in range(math.ceil(diff/interval)):
        count = helperFunctions.count_range_in_list(list(df["percentage_changes"]),a,b)
        k = "{}% to {}%".format(a, b)
        profit_loss_distribution[k] = count
        a += interval
        b += interval
    c = helperFunctions.count_range_in_list(list(df["percentage_changes"]),40,1000)
    k = "Greater than 40%"
    profit_loss_distribution[k] = c
    balance_percent_array_last20 = list(df["percentage_changes"])[-20:]
    mini = -40
    maxi = 40
    diff = int(maxi-mini)
    interval = 5
    a = math.floor(mini)
    b = math.ceil(a + interval)
    # Calculating profit/Loss(last 20 trades) distribution
    c = helperFunctions.count_range_in_list(balance_percent_array_last20,-1000,-40)
    k = "Greater than -40%"
    profit_loss_distribution_last_20[k] = c
    for r in range(math.ceil(diff/interval)):
        count = helperFunctions.count_range_in_list(balance_percent_array_last20,a,b)
        k = "{}% to {}%".format(a, b)
        profit_loss_distribution_last_20[k] = count
        a+=interval
        b+=interval
    c = helperFunctions.count_range_in_list(balance_percent_array_last20,40,1000)
    k = "Greater than 40%+"
    profit_loss_distribution_last_20[k] = c
    profit_loss = {}
    profit_loss['profit_loss_distribution'] = profit_loss_distribution
    profit_loss['profit_loss_distribution_last20'] = profit_loss_distribution_last_20
    performancePerPeriod = performance_per_period(df)
    #df_percent = np.concatenate((df, np.round_(balance_percent,2)), axis = 1)
    return (breaking_points,balance_np_array,profit_loss,performancePerPeriod)


def weeklyPerformanceCurve(df,req_week):
    #my_date = datetime.date.today() 
    #req_week = my_date.isocalendar()[1]
    breaking_points = {}
    df = df.tail(7)
    df['DATE'] = df['DATE'].astype('datetime64[ns]')
    # df['Week_number'] = df["DATE"].dt.week
    for date in df["DATE"]:
        balance = df.loc[df['DATE'] == date, 'balance'].iloc[0]
        # week = df.loc[df['DATE'] == date, 'Week_number'].iloc[0]
        # if week == req_week:
        breaking_points[str(date)[:10]] = round(balance,2)
    return breaking_points

def tradingCalander(startDate,endDate,df):
    startDate = datetime.strptime(startDate,'%Y-%m-%d')
    endDate = datetime.strptime(endDate, '%Y-%m-%d')
    res = {}
    mask = (df['DATE'] > startDate) & (df['DATE'] <= endDate)
    df = df.loc[mask]
    res["OverAll"] = getBasicCalc(df)
    res['OverAll']['win_percentage'] = round(((res['OverAll']['win_trade']/res['OverAll']['total_trades'])*100),2) if res['OverAll']['total_trades'] !=0 else None
    res['OverAll']['loss_percentage'] = 100 - res['OverAll']['win_percentage'] if res['OverAll']['win_percentage'] is not None else None
    delta = timedelta(days=1)
    new = df[(df.DATE > startDate) & (df.DATE <= endDate)]
    # df['DATE'] = df['DATE'].dt.strftime('%Y-%m-%d')
    res["calendarBydate"] = []
    import pandas as pd
    for d in new.DATE.unique():
        df_new = new.loc[new['DATE'] == d]
        r = getBasicCalc(df_new)
        r['Date'] = (pd.to_datetime(str(d))).strftime('%Y-%m-%d')
        r['DateNumber'] = (pd.to_datetime(str(d))).strftime('%Y-%m-%d')[8:]
        res["calendarBydate"].append(r)
    # while startDate <= endDate:
    #     startDate += delta
    #     strDate = str(startDate)[:10]
    #     df_new = df.loc[df['DATE'] == strDate]
    #     if df_new.empty:
    #         pass
    #     else:
    #         # print("df")
    #         # print(df_new)
    #         # print(strDate[8:])
    #         r = getBasicCalc(df_new)
    #         r['Date'] = strDate
    #         r['DateNumber'] = strDate[8:]
    #         res["calendarBydate"].append(r)
    #     df_new = df
    # print(len(res["calendarBydate"]))
    return res

def transactionsByDate(df,date):
    date = datetime.strptime(date,"%Y-%m-%d")
    df['DATE'] = df['DATE'].astype('datetime64[ns]')
    df = df.loc[df["DATE"] == date]
    res = []
    result = {}
    for i in df.index:
        result["DATE"] = str(df.loc[i, "DATE"])
        result["TRANSACTION ID"] = str(df.loc[i, "TRANSACTION ID"])
        result["DESCRIPTION"] = str(df.loc[i, "DESCRIPTION"])
        result["DESCRIPTION"] = str(df.loc[i, "DESCRIPTION"])
        result["SYMBOL"] = str(df.loc[i, "SYMBOL"])
        result["PRICE"] = str(df.loc[i, "PRICE"])
        result["AMOUNT"] = str(df.loc[i, "AMOUNT"])
        #result["p&l"] = str(df.loc[i, "p&l"])
        res.append(result)
    return {"status": codes.OK, "result": res, "message": messages.USER_DETAILS_FETCHED}


def getBasicCalc(df):
    res = {}
    total_gain = 0
    total_loss = 0
    win_trade = 0
    loss_trade = 0
    total_trades = len(list(df['p&l']))
    pl = df["p&l"]
    percentage = df["percentage_changes"]
    total_win_percent = 0
    win_percent_count = 0
    total_loss_percent = 0
    loss_percent_count = 0
    for j in percentage:
        if j >= 0:
            total_win_percent += j
            win_percent_count += 1
        else:
            total_loss_percent +=j
            loss_percent_count +=1

    res['avg_win_percentage'] = round(total_win_percent/win_percent_count,2) if win_percent_count != 0 else 0.0
    res['avg_loss_percentage'] = round(total_loss_percent/loss_percent_count,2) if loss_percent_count != 0 else 0.0

    count = 0
    for i in df.iloc[::-1]["balance"]:
        if count == 0:
            res['balance'] = round(i,2)
        count = count + 1
    for i in pl:
        if i >= 0:
            total_gain += i
            win_trade += 1
        else:
            total_loss += i
            loss_trade += 1
    res['avg_profit'] = round(total_gain/win_trade,2) if win_trade != 0 else 0.0
    res['avg_loss'] = round(total_loss/loss_trade,2) if loss_trade != 0 else 0.0
    res["total_gain"] = round(total_gain,2)
    res["total_loss"] = round(abs(total_loss),2)
    res["win_trade"] = win_trade
    res["loss_trade"] = loss_trade
    res["total_trades"] = total_trades

    return res


def calc_risk(entry_amount,df):
    res = {}
    risk_percent = (entry_amount *  .02)
    dim = df.shape
    risk_percent_array = []
    risk_percent_array_win = []
    risk_win_sum = 0
    risk_percent_array_loss = []
    risk_loss_sum = 0
    win_trade = 0
    loss_trade = 0
    for i in df['p&l']:
        r = round(i / risk_percent, 2) if risk_percent !=0 else 0
        risk_percent_array.append(r)
        if r >= 0:
            risk_percent_array_win.append(r)
            risk_win_sum += r
            win_trade+=1
        else:
            risk_percent_array_loss.append(r)
            risk_loss_sum += r
            loss_trade+=1
    win_rate = win_trade/(win_trade+loss_trade) if (win_trade+loss_trade) != 0 else 0
    """for i in range(1,dim[1]):
        for j in range(dim[0]):
            r = round(df[j][i]/risk_percent,2)
            risk_percent_monthwise[j][i-1] = r
            risk_percent_array.append(r)
            if r > 0:
                risk_percent_array_win.append(r)
                risk_win_sum += r
            else:
                risk_percent_array_loss.append(r)
                risk_loss_sum += r"""

    res['avg_profit_R'] = round(risk_win_sum/len(risk_percent_array_win),2) if len(risk_percent_array_win) != 0 else 0
    res['avg_loss_R'] = round(risk_loss_sum/len(risk_percent_array_loss),2) if len(risk_percent_array_loss) != 0 else 0
    res['req_winrate_perecent_for_profit_factor_per_trade'] = round((win_rate*(res['avg_profit_R']/res['avg_loss_R']))/(1-win_rate),2) if (win_rate != 1 and res['avg_loss_R'] !=0 ) else 0
    res['r_multiple_risk_reward_ratio'] = abs(round(res['avg_profit_R']/res['avg_loss_R'],2)) if res['avg_loss_R'] != 0 else 0
    res['avg_win_percentage'] = round(risk_win_sum/res['avg_profit_R'],2) if res['avg_profit_R'] !=0 else 0
    res['avg_loss_percentage'] = round(risk_loss_sum / res['avg_loss_R'],2) if res['avg_loss_R'] !=0 else 0
    res['largest_win_percentage'] = round(max(risk_percent_array)/res['avg_profit_R'],2)*100 if res['avg_profit_R'] !=0 else 0
    res['largest_loss_percentage'] = round(min(risk_percent_array)/res['avg_loss_R'], 2) * 100 if res['avg_loss_R'] !=0 else 0
    res['req_win_perencetage_to_breakdown'] = round(abs(res['avg_loss_R'])/(res['avg_profit_R']+abs(res['avg_loss_R'])),2)*100 if res['avg_profit_R'] !=0 else 0
    res['R_multiple_expectancy_per_trade'] = round(sum(risk_percent_array)/len(risk_percent_array),2) if len(risk_percent_array) != 0 else 0
    res['R_mutliple_adjusted_RRR'] = round(risk_win_sum/abs(risk_loss_sum),2) if risk_loss_sum else 0
    res['planned_RRR'] = round((3*win_rate-1), 2) 
    return res






def overall_performance(df, entry_amount=None, last=None):
    if df.empty and last != None:
        return "Please Upload CSV first"
    elif df.empty:
        return {"status": codes.OK, "result": "Please Upload CSV first", "message": messages.DATA_NOT_CALCULATED}
    res = {}
    total_gain = 0
    total_loss = 0
    win_trade = 0
    loss_trade = 0
    dim = df.shape
    all_trades = []
    total_trades = len(list(df['p&l']))
    if last == None:
        last = total_trades
    check = total_trades-last
    counter=-1
    if last == None:
        pl = df["p&l"]
        percentage = df['percentage_changes']
    else:
        pl = df["p&l"].tail(last)
        percentage = df['percentage_changes'].tail(last)
    for i in pl:
        if i >= 0:
            total_gain += i
            win_trade+=1
        else:
            total_loss += i
            loss_trade+=1
    total_win_percent = 0
    win_percentage_count = 0
    total_loss_percent = 0
    loss_percentage_count = 0
    for j in percentage:
        if j >= 0:
            total_win_percent += j
            win_percentage_count +=1
        else:
            total_loss_percent += j
            loss_percentage_count +=1



    # print({"gain":total_gain, "loss": total_loss})       
    gain_by_loss = round(total_gain+total_loss,2)
    # average_profit = total_gain-total_loss/total_gain
    average_profit = total_gain/win_trade if win_trade != 0 else 0
    
    average_loss = total_loss/loss_trade if loss_trade != 0 else 0
    win_percentage = round((win_trade/(win_trade+loss_trade))*100, 2)
    loss_percentage = 100 - win_percentage
    profit_rate = round((average_profit/(average_profit-(average_loss)))*100, 2)
    
    loss_rate = 100 - profit_rate
    profit_factor = round((-1)*(total_gain/total_loss),2) if total_loss != 0 else 0
    res['total_gain'] = round(total_gain,2)
    res['total_loss'] = round(total_loss,2)
    res['win_trade'] = win_trade
    res['loss_trade'] = loss_trade
    res['avg_holding_days_on_winners'] = round(total_gain/win_trade,2) if win_trade !=0 else 0
    res['avg_holding_days_on_lossers'] = round(total_loss/loss_trade,2) if loss_trade !=0 else 0
    res['avg_holding_days'] = round((total_gain+total_loss)/(loss_trade+win_trade),2)
    win_rate1 = win_percentage/100
    res['total_trades'] = win_trade+loss_trade
    res['win_loss_ratio'] = round(win_trade/loss_trade,2) if loss_trade != 0 else 0
    res['gain_by_loss'] = round(gain_by_loss,2) 
    res['average_profit'] = round(average_profit,2)
    res["average_profit_percentage"] = round(((average_profit + (average_loss))/average_profit) * 100, 2) if average_profit != 0 else 0
    res['average_loss'] = round(average_loss,2)
    res['profitlossEdgeRatio'] = round(average_profit/average_loss,2) if average_loss != 0 else 0
    res['adjustProfitLossRatio'] = round(res['profitlossEdgeRatio'] * res['win_loss_ratio'],2)
    res['win_percentage'] = win_percentage
    res['loss_percentage'] = loss_percentage
    res['profit_rate'] = profit_rate
    res['loss_rate'] = loss_rate
    res['profit_factor'] = profit_factor
    res['largestProfit'] = df["p&l"].max()
    res['largestLost'] = df["p&l"].min()
    res['avg_win_percentage'] = round(total_win_percent/win_percentage_count,2) if win_percentage_count !=0 else 0
    res['avg_loss_percentage'] = round(total_loss_percent/loss_percentage_count,2) if loss_percentage_count != 0 else 0
    res['largest_win_percentage'] = round((df['percentage_changes'].max()/res['avg_win_percentage'])*100,2) if res['avg_win_percentage'] != 0 else 0
    res['largest_loss_percentage'] = round((df['percentage_changes'].min()/res['avg_loss_percentage'])*100,2) if res['avg_loss_percentage'] != 0 else 0
    if last != None and entry_amount != None:
        # print(df.tail(30))
        new_df = df.tail(30)
        risk = calc_risk(entry_amount, new_df)
        res["adjusted_rrr"] = risk["R_mutliple_adjusted_RRR"]
        res['RRR'] = abs(risk['r_multiple_risk_reward_ratio'])

    if entry_amount != None:
        result = calc_risk(entry_amount, new_df)
        reward = result['avg_profit_R']
        risk = result['avg_loss_R']
        res['expectancy'] = round(((win_rate1*reward)-(1-win_rate1)*risk), 2)
    if check==0:
        return {"status": codes.OK, "result": res, "message": messages.DATA_CALCULATED}
    else:
        return res

def top_bottom_stocks(df):
    res = {}
    top = {}
    bottom = {}
    dim = df.shape
    df = df[df[:,dim[1]-1].argsort()]
    for i in range(3):
        top[str(i+1)] = {}
        top[str(i+1)]['Cumulative P&L']= round(df[(dim[0]-1)-i][dim[1]-1],2)
        top[str(i+1)]['Stock Name']= df[(dim[0]-1)-i][0]
        bottom[str(i+1)] = {}
        bottom[str(i+1)]['Cumulative P&L'] = round(df[i][dim[1]-1],2)
        bottom[str(i+1)]['Stock Name'] = df[i][0]
    res['TOP3'] = top
    res['BOTTOM3'] = bottom
    return res


def find_headers(df):
    header = []
    for columns in df:
        header.append(columns)

    return header


def draw_down(df):
    dim = df.shape
    # npl = []
    res = {}
    npl = list(df["p&l"])
    balance = list(df['balance'])
    # for i in range(1,dim[1]):
    #     for j in range(dim[0]):
    #         npl.append(df[j][i])
    r = services.user.max_dradown(balance)
    res['max_drawdown_amount'] = r['max_drawdown_amount']
    res['max_drawdown_percent'] = r['max_drawdown_percent']
    res['win_loss_streak'] = services.user.streak(npl)
    res['largest_win_loss'] = services.user.largest_smallest_streak(npl)
    return res

def tradeSetup(db,id):
    UID = db.users.find_one({"_id": ObjectId(id)},{"UID":1,"_id":0})["UID"]
    allSetups = [None,'Momentum','Bounce','Trends Flow','Swing Table','Bottom Fishing']
    res = {}
    for setup in allSetups:
        res[setup] = {}
        doc = db.transactions.find({"UID":UID,"setup":setup})
        total_trades = doc.count()
        res[setup]['count'] = total_trades
        wins = 0
        p_l = 0

        for i in doc:

            if float(i['p&l']) > 0:
                wins+=1
            p_l += float(i['p&l'])
        res[setup]['winPercent'] = round((wins/total_trades)*100,2) if total_trades != 0 else 0.0
        res[setup]['profitLoss'] = round(p_l,2)
    return res

def tradeEvaluation(db,id):
    UID = db.users.find_one({"_id": ObjectId(id)}, {"UID": 1, "_id": 0})["UID"]
    entryLevels = ['Too Late',"Too Early","Not in Plan","Planned","Broke Rule","News","Funda"]
    emotions = ["Fear","Hope","Greed","Bored","Impulse","Fomo","Confident","Hype"]
    res = {}
    res["EntryLevel"] = {}
    res["Emotions"] = {}
    for i in entryLevels:
        doc = db.transactions.find({"UID":UID,"entryLevel":i})
        res["EntryLevel"][i] = doc.count()
    for j in emotions:
        doc = db.transactions.find({"UID":UID,"emotion":j})
        res["Emotions"][j] = doc.count()
    return res

def emptyDF():
    return {"status": codes.BAD_REQUEST, "result": "Please upload a CSV first", "message": messages.DATA_NOT_CALCULATED}

















