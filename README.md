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
from collections import OrderedDict
from pandas.io.json import json_normalize
```
The following are imported:  
* pandas - dataframe manipulation
* tweepy - Twitter APIs
* time - while loop
* OrderedDict - ordering JSON files
* json_normalize - normalizing JSON files
```python
try:
    consumer_key = ""
    consumer_secret = ""
    access_key = ""
    access_secret = ""
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    
except:
    print('Error. Authentication failed.')
```
Standard Twitter authorisation. Create your own app and obtain your own keys via [Twitter apps](https://developer.twitter.com/en/apps).
```python
api = tweepy.API(auth, parser = tweepy.parsers.JSONParser())
searchterm = input('Enter your search term: ')
searchquery = '"' + searchterm + '" -filter:retweets -filter:media -filter:images -filter:links'
data = api.search(q = searchquery, lang = 'en', count = 100, result_type = 'mixed')
data = OrderedDict(data)
data_all = list(data.values())[0]
```
Program prompts for search term. Search term is appended to full search query filtering out retweets, media, images and links. 
Twitter API returns results in a JSON file. JSON file is ordered and tweets are extracted to a separate list. 
```python
maxtweets = 1000

while (len(data_all) < maxtweets):
    time.sleep(5)
    last_id = data_all[-1]['id']
    data = api.search(q = searchquery, lang = 'en', count = 100, result_type = 'mixed', max_id = last_id)
    data = OrderedDict(data)
    data_all_temp = list(data.values())[0]
    data_all += data_all_temp

df = pd.DataFrame.from_dict(json_normalize(data_all), orient='columns')
```
Twitter API limits 100 tweets per call. A target number of tweets to mine is set (i.e. 1000) and the while loop repeatedly calls the API referencing the last tweet ID and appends the list 100 tweets at a time until the targeted number of tweets is met. The resulting list is converted into a dataframe for further manipulation. 
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
VADER model is imported and separate functions are defined to return compound, positive, negative and neutral scores. 
```python
df2 = pd.DataFrame()
df2['id'] = df['id'].values
df2['created_at'] = df['created_at'].values
df2['tweet'] = df['text'].values
df2['vs_compound'] = df.apply(lambda row: sentiment_score_compound(row['text']), axis=1)
df2['vs_pos'] = df.apply(lambda row: sentiment_score_pos(row['text']), axis=1)
df2['vs_neg'] = df.apply(lambda row: sentiment_score_neg(row['text']), axis=1)
df2['vs_neu'] = df.apply(lambda row: sentiment_score_neu(row['text']), axis=1)

header = ['id', 'created_at', 'tweet', 'vs_compound', 'vs_pos', 'vs_neg', 'vs_neu']
timestr = time.strftime("%Y%m%d-%H%M%S")
df2.to_csv('output-'+timestr+'.csv', columns = header)
```
Output dataframe (df2) is defined importing desired columns from tweets dataframe (df). Sentiment scores columns are generated applying respective functions to the tweet. Final dataframe is output into a .csv file. 

### Limitations / Improvements
1. Twitter public APIs restrict getting of tweets up to a maximum of 7 days. 
2. Large amount of tweets have geocodes disabled, so it is difficult to mine location-specific tweets. 
3. While loop does not break if less than maxtweets are mined. 
4. Introducing regex to clean tweet text by removing special characters
