import pandas as pd
import tweepy
import time
import sys
from collections import OrderedDict
from pandas.io.json import json_normalize

consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""
    
def initialize():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth, parser = tweepy.parsers.JSONParser())
    return api

api = initialize()

print('\nThis program gets tweets using Twitter public APIs and passes them through the VADER sentiment analysis model - a model geared towards social media sentiment analysis. Results are generated in a .csv file output for further analysis.')    
geo_enabled = input('Run geo-enabled search? (y/n): ').lower().strip()

while geo_enabled not in ('y','n'):
    print('Invalid input. Please enter y/n: ')
    geo_enabled = input().lower().strip()
     
if geo_enabled[0] == 'y':
    country = input('Enter your country: ')
    geocode = api.geo_search(query = country)
    geocode = OrderedDict(geocode)

    while geocode['result']['places'] == []:
        print('\n No results found. Please try again.')
        country = input('Enter your country: ')
        geocode = api.geo_search(query = country)
        geocode = OrderedDict(geocode)

    #api.geo_search returns coordinates in 'longitude, latitude' but api.search geocode parameter is defined by 'LATitude, LONGitude'
    latitude = float(geocode['result']['places'][0]['centroid'][1])
    longitude = float(geocode['result']['places'][0]['centroid'][0])
    print('The lat-long coordinates for the country are ', latitude, ' ', longitude)
    max_range = int(input('Input radius of search in kilometres: '))
    searchterm = input('Enter your search term: ')
    searchquery = searchterm + ' -filter:retweets -filter:media -filter:images -filter:links'
    data = api.search(q = searchquery, geocode = "%f,%f,%dkm" % (latitude, longitude, max_range), lang = 'en', count = 100, result_type = 'mixed')

else:
    searchterm = input('Enter your search term: ')
    searchquery = searchterm + ' -filter:retweets -filter:media -filter:images -filter:links'
    data = api.search(q = searchquery, lang = 'en', count = 100, result_type = 'mixed')

data = OrderedDict(data)
data_all = list(data.values())[0]
max_tweets = input('Enter number of requested tweets (recommended less than 1,000): ')
max_tweets = int(max_tweets)

if data_all == []:
    print('\n No results found. Program will terminate.')
    sys.exit()
    
done = False

if len(data_all) < 100:
    done = True

while not done:
    last_id = data_all[-1]['id']
    data = api.search(q = searchquery, lang = 'en', count = 100, result_type = 'mixed', max_id = last_id)      
    data = OrderedDict(data)
    data_all_temp = list(data.values())[0]
    data_all += data_all_temp
    time.sleep(1)
    
    if data_all_temp == []:
        done = True
        
    if len(data_all_temp) < 100:
        done = True
        
    if len(data_all) >= max_tweets:
        done = True

df = pd.DataFrame.from_dict(json_normalize(data_all), orient='columns')

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

df2 = pd.DataFrame()
df2['id'] = df['id'].values
df2['created_at'] = df['created_at'].values
df2['user.screen_name'] = df['user.screen_name'].values
df2['place.country'] = df['place.country'].values
df2['tweet'] = df['text'].values
df2['vs_compound'] = df.apply(lambda row: sentiment_score_compound(row['text']), axis=1)
df2['vs_pos'] = df.apply(lambda row: sentiment_score_pos(row['text']), axis=1)
df2['vs_neg'] = df.apply(lambda row: sentiment_score_neg(row['text']), axis=1)
df2['vs_neu'] = df.apply(lambda row: sentiment_score_neu(row['text']), axis=1)

no_pos_tweets = [tweet for index, tweet in enumerate(df2['vs_compound']) if df2['vs_compound'][index] > 0]
no_neg_tweets = [tweet for index, tweet in enumerate(df2['vs_compound']) if df2['vs_compound'][index] < 0]
no_neu_tweets = [tweet for index, tweet in enumerate(df2['vs_compound']) if df2['vs_compound'][index] == 0]

print(len(df2), 'tweets found.')
print('\rPercentage of positive tweets: {:.2f}%'.format(len(no_pos_tweets)*100/len(df2['vs_compound'])))
print('\rPercentage of negative tweets: {:.2f}%'.format(len(no_neg_tweets)*100/len(df2['vs_compound'])))
print('\rPercentage of neutral tweets: {:.2f}%'.format(len(no_neu_tweets)*100/len(df2['vs_compound'])))

header = ['id', 'created_at', 'user.screen_name', 'place.country', 'tweet', 'vs_compound', 'vs_pos', 'vs_neg', 'vs_neu']
timestr = time.strftime("%Y%m%d-%H%M%S")
df2.to_csv('output-'+timestr+'.csv', columns = header)
print('\nOutput saved as output-',timestr,'.csv')
