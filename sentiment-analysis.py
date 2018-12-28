# -*- coding: utf-8 -*-
"""
Created on Fri Dec 28 02:37:30 2018

@author: danne.wong
"""

import pandas as pd
import os
import matplotlib.pyplot as plt
import tweepy
import json
import time
from collections import OrderedDict
from pandas.io.json import json_normalize

#Confirm working directory
print("The current working directory is {}" .format(os.getcwd()))

#Twitter authorisations
consumer_key = "j2n9h4nuyesbpLuMmp1ZSIO1Q"
consumer_secret = "avKgXbusEqWv7EQm7djdS92GDdaz3EUB6HnU8e07jue1eF3VLf"
access_key = "1077042993385725952-sIPkqtiQyZGbMNDc8oQPH6bx7bSn4g"
access_secret = "C7Ct7OSHfuXxrpyFQhTXlU9AfYKYYsboUHvw9eMA9VX12"

#Twitter mining
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth, parser = tweepy.parsers.JSONParser())

#searchterm = input('Enter your search term: ')
searchquery = 'Obama' + ' -filter:retweets -filter:media -filter:images -filter:links'

maxtweets = 400
data = api.search(q = searchquery, lang = 'en', count = 100, result_type = 'mixed')
data = OrderedDict(data)
data_all = list(data.values())[0]

while (len(data_all) < maxtweets):
    time.sleep(5)
    last_id = data_all[-1]['id']
    data = api.search(q = searchquery, lang = 'en', count = 100, result_type = 'mixed', max_id = last_id)
    data = OrderedDict(data)
    data_all_temp = list(data.values())[0]
    data_all += data_all_temp

df = pd.DataFrame.from_dict(json_normalize(data_all), orient='columns')

#Using VADER sentiment model
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
analyzer = SentimentIntensityAnalyzer()

def sentiment_score_compound(sentence):
    score = analyzer.polarity_scores(sentence)
    return score['compound']

def sentiment_score_pos(sentence):
    score = analyzer.polarity_scores(sentence)
    return score['pos']

def sentiment_score_neg(sentence):
    score = analyzer.polarity_scores(sentence)
    return score['neg']

def sentiment_score_neu(sentence):
    score = analyzer.polarity_scores(sentence)
    return score['neu']

#Consolidating cols for output
df2 = pd.DataFrame()
df2['id'] = df['id'].values
df2['created_at'] = df['created_at'].values
df2['tweet'] = df['text'].values
df2['vs_compound'] = df.apply(lambda row: sentiment_score_compound(row['text']), axis=1)
df2['vs_pos'] = df.apply(lambda row: sentiment_score_pos(row['text']), axis=1)
df2['vs_neg'] = df.apply(lambda row: sentiment_score_neg(row['text']), axis=1)
df2['vs_neu'] = df.apply(lambda row: sentiment_score_neu(row['text']), axis=1)

header = ['id', 'created_at', 'tweet', 'vs_compound', 'vs_pos', 'vs_neg', 'vs_neu']

#filename
timestr = time.strftime("%Y%m%d-%H%M%S")
df2.to_csv('essence_output'+timestr+'.csv', columns = header)
 