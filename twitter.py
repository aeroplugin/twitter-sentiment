import os
from flask import Flask, render_template, request
import tweepy
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

nltk.download('vader_lexicon')

app = Flask(__name__)

BEARER_TOKEN = os.environ.get('replace with bearer_token', 'replace with bearer_token')
client = tweepy.Client(bearer_token=BEARER_TOKEN)

def analyze_entity(entity, category):
    query = f'{entity} {category} -is:retweet lang:en'
    
    try:
        tweets = client.search_recent_tweets(
            query=query,
            max_results=25,
            tweet_fields=['public_metrics', 'text']
        )
        
        if not tweets.data:
            return None
            
    except tweepy.TweepyException as e:
        print(f"Twitter API error: {e}")
        return None

    sia = SentimentIntensityAnalyzer()
    metrics = {
        'tweets': len(tweets.data) if tweets.data else 0,
        'impressions': 0,
        'comments': 0,
        'reposts': 0,
        'likes': 0,
        'sentiment': {'positive': 0, 'neutral': 0, 'negative': 0}
    }
    
    if tweets.data:
        for tweet in tweets.data:
            metrics['impressions'] += tweet.public_metrics['impression_count']
            metrics['comments'] += tweet.public_metrics['reply_count']
            metrics['reposts'] += tweet.public_metrics['retweet_count']
            metrics['likes'] += tweet.public_metrics['like_count']
            
            score = sia.polarity_scores(tweet.text)['compound']
            if score > 0.05:
                metrics['sentiment']['positive'] += 1
            elif score < -0.05:
                metrics['sentiment']['negative'] += 1
            else:
                metrics['sentiment']['neutral'] += 1
        
        total = metrics['tweets']
        for sentiment in metrics['sentiment']:
            metrics['sentiment'][sentiment] = round(
                metrics['sentiment'][sentiment] / total * 100, 1
            ) if total else 0
    
    return metrics

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    company = request.form['company']
    category = request.form['category']
    
    entities = [company]
    results = {}
    
    for entity in entities:
        analysis = analyze_entity(entity, category)
        if analysis:
            results[entity] = analysis
    
    return render_template('results.html', results=results, category=category)

if __name__ == '__main__':
    app.run(debug=True)