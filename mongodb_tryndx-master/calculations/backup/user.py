import numpy as np
from constants import *
from validations import helperFunctions

def calc_cummulative_pnl(df):
    dim = df.shape
    cummulative_pl = np.zeros((26, 1), dtype="int64")
    for i in range(dim[0]):
        cpl = 0
        for j in range(1, dim[1]):
            cpl += df[i][j]
        cummulative_pl[i][0] = cpl
    df = np.concatenate((df, cummulative_pl), axis=1)
    return df


def performance_per_period(breaking_points):
    last3MonthKeys = []
    last6MonthKeys = []
    lastYearKeys = []
    allTimeKeys = []
    #for last month

    res = {}
    keys = list(breaking_points.keys())
    allTimeKeys.append(keys[0])
    allTimeKeys.append(keys[-1])
    profit_loss = breaking_points[allTimeKeys[1]] - breaking_points[allTimeKeys[0]]
    profit_loss_percent = str(round(profit_loss / breaking_points[allTimeKeys[1]], 5) * 100) + '%'
    res['allTime'] = (profit_loss, profit_loss_percent)

    if len(keys) > 1:
        last_month_keys = keys[-2:]
        profit_loss = breaking_points[last_month_keys[1]] - breaking_points[last_month_keys[0]]
        profit_loss_percent = str(round(profit_loss/breaking_points[last_month_keys[1]],5)*100) + '%'
        res['LastMonth'] = (profit_loss,profit_loss_percent)
    else:
        res['LastMonth'] = None

    if len(keys)>2:
        last3MonthKeys.append(keys[-3])
        last3MonthKeys.append(keys[-1])
        profit_loss = breaking_points[last3MonthKeys[1]] - breaking_points[last3MonthKeys[0]]
        profit_loss_percent = str(round(profit_loss / breaking_points[last3MonthKeys[1]], 5) * 100) + '%'
        res['LastThreeMonth'] = (profit_loss, profit_loss_percent)
    else:
        res['LastThreeMonth'] = None

    if len(keys)>5:
        last6MonthKeys.append(keys[-3])
        last6MonthKeys.append(keys[-1])
        profit_loss = breaking_points[last3MonthKeys[1]] - breaking_points[last3MonthKeys[0]]
        profit_loss_percent = str(round(profit_loss / breaking_points[last3MonthKeys[1]], 5) * 100) + '%'
        res['LastSixMonth'] = (profit_loss, profit_loss_percent)
    else:
        res['LastSixMonth'] = None

    if len(keys)>11:
        lastYearKeys.append(keys[-3])
        lastYearKeys.append(keys[-1])
        profit_loss = breaking_points[last3MonthKeys[1]] - breaking_points[last3MonthKeys[0]]
        profit_loss_percent = str(round(profit_loss / breaking_points[last3MonthKeys[1]], 5) * 100) + '%'
        res['LastYear'] = (profit_loss, profit_loss_percent)
    else:
        res['LastYear'] = None

    return res









def monthwise_balance(balance,df,headers):
    breaking_points = {}
    dim = df.shape
    balance_np_array = []
    balance_np = np.zeros((dim[0], dim[1]-1), dtype = "int64")
    balance_percent = np.zeros((dim[0], dim[1]-1), dtype = "float")
    balance_percent_array = []
    for i in range(1,dim[1]):
        breaking_points[headers[i-1]] = int(balance)
        for j in range(dim[0]):
            balance_np_array.append(int(balance + int(df[j][i])))
            balance_np[j][i-1] = balance + df[j][i]
            percent = round((df[j][i])/balance,5)
            balance_percent_array.append(percent*100)
            balance_percent[j][i-1] = (percent*100)
            balance = balance_np[j][i-1]
    df_bal = np.concatenate((df, balance_np), axis = 1)

    mini = min(balance_percent_array)
    maxi = max(balance_percent_array)
    diff = int(maxi-mini)
    profit_loss_distribution = {}
    profit_loss_distribution_last_20 = {}
    a = int(mini) - 1
    b = a + 1
    #Calculating profit/Loss distribution
    for r in range(diff+2):
        count = helperFunctions.count_range_in_list(balance_percent_array,a,b)
        k = str(a) + '% - ' + str(b) + '%'
        profit_loss_distribution[k] = count
        a+=1
        b+=1



    balance_percent_array_last20 = balance_percent_array[-20:]

    mini = min(balance_percent_array_last20)
    maxi = max(balance_percent_array_last20)
    diff = int(maxi-mini)
    a = int(mini) - 1
    b = a + 1
    # Calculating profit/Loss(last 20 trades) distribution
    for r in range(diff+2):
        count = helperFunctions.count_range_in_list(balance_percent_array_last20,a,b)
        k = str(a) + '% - ' + str(b) + '%'
        profit_loss_distribution_last_20[k] = count
        a+=1
        b+=1

    profit_loss = {}
    profit_loss['profit_loss_distribution'] = profit_loss_distribution
    profit_loss['profit_loss_distribution_last20'] = profit_loss_distribution_last_20

    performancePerPeriod = performance_per_period(breaking_points)

    #df_percent = np.concatenate((df, np.round_(balance_percent,2)), axis = 1)




    return (breaking_points,balance_np_array,profit_loss,performancePerPeriod)


def calc_risk(balance,df):
    risk_percent = (balance *  .02)
    dim = df.shape
    risk_percent_monthwise = np.zeros((dim[0], dim[1] - 1), dtype="float")
    for i in range(1,dim[1]):
        for j in range(dim[0]):
            risk_percent_monthwise[j][i-1] = round(df[j][i]/risk_percent,2)

    df_risk_precentage = np.concatenate((df,risk_percent_monthwise),axis = 1)
    return df_risk_precentage


def overall_performance(df):
    res = {}
    total_gain = 0
    total_loss = 0
    win_trade = 0
    loss_trade = 0
    dim = df.shape
    for i in range(1,dim[1]):
        for j in range(dim[0]):
            if df[j][i] > 0:
                total_gain += df[j][i]
                win_trade+=1
            else:
                total_loss += df[j][i]
                loss_trade+=1
    gain_by_loss = total_gain+total_loss
    average_profit = total_gain/win_trade
    average_loss = total_loss/loss_trade
    win_percentage = round((win_trade/(win_trade+loss_trade))*100)
    loss_percentage = 100 - win_percentage
    profit_rate = round(average_profit/(average_profit-average_loss))*100
    loss_rate = 100 - profit_rate
    profit_factor = round((-1)*(total_gain/total_loss),2)
    res['total_gain'] = total_gain
    res['total_loss'] = total_loss
    res['win_trade'] = win_trade
    res['loss_trade'] = loss_trade
    res['gain_by_loss'] = gain_by_loss
    res['average_profit'] = average_profit
    res['average_loss'] = average_loss
    res['win_percentage'] = win_percentage
    res['loss_percentage'] = loss_percentage
    res['profit_rate'] = profit_rate
    res['loss_rate'] = loss_rate
    res['profit_factor'] = profit_factor

    return {"status": codes.OK, "result": res, "message": messages.DATA_CALCULATED}



def top_bottom_stocks(df):
    res = {}
    top = {}
    bottom = {}
    dim = df.shape
    df = df[df[:,dim[1]-1].argsort()]
    for i in range(3):
        top[str(i+1)] = {}
        top[str(i+1)]['Cumulative P&L']= df[(dim[0]-1)-i][dim[1]-1]
        top[str(i+1)]['Stock Name']= df[(dim[0]-1)-i][0]
        bottom[str(i+1)] = {}
        bottom[str(i+1)]['Cumulative P&L'] = df[i][dim[1]-1]
        bottom[str(i+1)]['Stock Name'] = df[i][0]
    res['TOP 3'] = top
    res['BOTTOM 3'] = bottom
    return res


def find_headers(df):
    header = []
    for columns in df:
        header.append(columns)
    del header[0]
    return header





