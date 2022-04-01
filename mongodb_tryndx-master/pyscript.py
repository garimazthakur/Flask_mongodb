import json
import pymongo
import pandas as pd
import csv
myclient = pymongo.MongoClient()

database = myclient['trendx']
collection = database['ticker']

df = pd.read_csv('polygon_tickers.csv')
df.to_json('yourjson.json')
jdf = open('yourjson.json').read()                       
data = json.loads(jdf)

#collection.insert_many(dict(data))

with open('polygon_tickers_us.csv', 'r') as read_obj:
    csv_reader = csv.DictReader(read_obj)
    mylist = list(csv_reader)
    collection.insert_many(mylist)