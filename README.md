# sentiment-analysis-twitter
This script gets tweets using Twitter public APIs and passes them through the VADER sentiment analysis model - a model geared towards social media sentiment analysis. Results are generated in a .csv file output for further analysis.  

### VADER Sentiment Analysis Model

VADER (Valence Aware Dictionary and sEntiment Reasoner) is a lexicon and rule-based sentiment analysis tool that is specifically attuned to sentiments expressed in social media. More details can be found in:

* [cjhutto](https://github.com/cjhutto/vaderSentiment) - VADER Sentiment GitHub Repository

## Prerequisites

Install Python and the packages that is required to run this script. If you use Anaconda, most of these packages should already be installed. You will likely need to install the vaderSentiment package. Do so via the command prompt: 

```python
pip install vaderSentiment
```

## Script

```python
import pandas as pd
import tweepy
import time
import sys
from collections import OrderedDict
from pandas.io.json import json_normalize
```
The following are imported:  
* pandas - dataframe manipulation
* tweepy - Twitter APIs
* time - while loop
* sys - kill program
* OrderedDict - ordering JSON files
* json_normalize - normalizing JSON files
```python
consumer_key = ""
consumer_secret = ""
access_key = ""
access_secret = ""
    
#Twitter authorisation
def initialize():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth, parser = tweepy.parsers.JSONParser())
    return api

api = initialize()
```
Standard Twitter authorisation. Create your own app and obtain your own keys via [Twitter apps](https://developer.twitter.com/en/apps).
```python
searchterm = input('Enter your search term: ')
searchquery = '"' + searchterm + '" -filter:retweets -filter:media -filter:images -filter:links'
data = api.search(q = searchquery, lang = 'en', count = 100, result_type = 'mixed')
data = OrderedDict(data)
data_all = list(data.values())[0]

max_tweets = input('Enter number of requested tweets (recommended less than 1,000): ')
max_tweets = int(max_tweets)

if data_all == []:
    print('\n No results found. Program will terminate.')
    sys.exit()
```
Program prompts user for search term and appends to searchquery (filtering out retweets, media, images and links) and requested amount of tweets (max_tweets). It performs first 100 searches. Twitter API limits 100 tweets per call, so a while loop has to be set up later to repeatedly call this API. Exception handling in place in the event of no tweets.  
```python
done = False

while not done:
    last_id = data_all[-1]['id']
    data = api.search(q = searchquery, lang = 'en', count = 100, result_type = 'mixed', max_id = last_id)      
    data = OrderedDict(data)
    data_all_temp = list(data.values())[0]
    data_all += data_all_temp
    time.sleep(1)
    
    if data_all_temp == []:
        done = True
        
    if len(data_all) >= max_tweets:
        done = True

df = pd.DataFrame.from_dict(json_normalize(data_all), orient='columns')
```
While loop repeatedly calls the API referencing the last tweet ID and appends the list 100 tweets at a time until the requested number of tweets is met. Results are returned in a JSON file. JSON file is ordered and tweets are extracted to a separate list. The resulting list is converted into a dataframe for further manipulation.
```python
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
```
Import VADER model and using its methods, define separate functions to return compound, positive, negative and neutral scores. 
```python
df2 = pd.DataFrame()
df2['id'] = df['id'].values
df2['created_at'] = df['created_at'].values
df2['user.screen_name'] = df['user.screen_name'].values
df2['tweet'] = df['text'].values
df2['vs_compound'] = df.apply(lambda row: sentiment_score_compound(row['text']), axis=1)
df2['vs_pos'] = df.apply(lambda row: sentiment_score_pos(row['text']), axis=1)
df2['vs_neg'] = df.apply(lambda row: sentiment_score_neg(row['text']), axis=1)
df2['vs_neu'] = df.apply(lambda row: sentiment_score_neu(row['text']), axis=1)

header = ['id', 'created_at', 'user.screen_name', 'tweet', 'vs_compound', 'vs_pos', 'vs_neg', 'vs_neu']
timestr = time.strftime("%Y%m%d-%H%M%S")
df2.to_csv('output-'+timestr+'.csv', columns = header)

print(len(df2), 'tweets found.')
print('Output saved as output-',timestr,'.csv')
```
Output dataframe (df2) is defined importing desired columns from tweets dataframe (df). Sentiment scores columns are generated applying respective functions to the tweet. Final dataframe is output into a .csv file. 

### Limitations / Improvements
1. Twitter public APIs restrict getting of tweets up to a maximum of 7 days. 
2. Majority of tweets have geocodes disabled, so it is difficult to mine location-specific tweets. 
3. Introducing regex to clean tweet text by removing special characters
