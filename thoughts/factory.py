# factory.py

import os
import flask
from flask import Flask
from flask_pymongo import PyMongo
from flask import render_template
import requests
import json
from bson.json_util import dumps



def create_app():

    MONGODB_URI = os.getenv('MONGODB_URI')
    DAVINCI_URL = "https://api.openai.com/v1/engines/davinci/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer sk-YQGRVYEvq9NVP7nXFnDdC0CL7aojDcBYMU9n3Nxu"
    }

    default_prompt = """
    Tweet: Take feedback from nature and markets, not from people.
    Tweet: Maybe we die so we can come back as children.
    Tweet: Startups shouldn’t worry about how to put out fires, they should worry about how to start them.
    Tweet:"""

    key_prompt = """
    key: markets
    tweet: Take feedback from nature and markets, not from people.
    key: children
    tweet: Maybe we die so we can come back as children.
    key: startups
    tweet: Startups shouldn’t worry about how to put out fires, they should worry about how to start them.
    key: {}
    tweet:"""

    data = {
      "max_tokens": 40,
      "temperature": 1,
      "top_p": 1,
      "n": 1,
      "stream": False,
      "logprobs": None,
      "stop": "\n"
    }

    app = Flask(__name__)
    app.config['MONGO_URI'] = MONGODB_URI
    mongo = PyMongo(app)

    @app.route('/', defaults={'key': None}, methods=['GET'])
    @app.route('/<key>', methods=['GET'])
    def load_tweet(key):

        data['prompt'] = key_prompt.format(key) if key else default_prompt

        # Get Tweet
        # try:
        #     response = requests.post(DAVINCI_URL, headers=headers, data=json.dumps(data))
        #     res = response.json()
        #     tweet = res['choices'][0]['text'].strip()
        # except Exception as e:
        #     print(e)
        #     page_views = mongo.db['page_views']
        #     cursor = page_views.aggregate([{'$match': {'key': key }}, {'$sample': { 'size': 1}}])
        #     record = json.loads(dumps(cursor))[0]
        #     print(record)
        #     tweet = record['tweet']
        # print(tweet)

        # Get tweet by key
        page_views = mongo.db['page_views']
        try:
            cursor = page_views.aggregate([{'$match': {'key': key }}, {'$sample': {'size': 1}}])
            record = json.loads(dumps(cursor))[0]
        except Exception as e:
            print("No match by key: {}".format(e))
            # Get tweet by regex
            try:
                cursor = page_views.aggregate([{'$match': {'tweet': {'$regex': key}}}, {'$sample': {'size': 1}}])
                record = json.loads(dumps(cursor))[0]
            except Exception as e:
                print("No match for regex: {}".format(e))
                # Get random tweet
                try:
                    cursor = page_views.aggregate([{'$sample': { 'size': 1}}])
                    record = json.loads(dumps(cursor))[0]
                except Exception as e:
                    print("Error in random tweet selection: {}".format(e))

        try:
            tweet = record['tweet']
        except Exception as e:
            print(e)
            tweet = "Oops! Something wasn't right. Please try again!"

        print(tweet)

        # Save data
        ip_address = flask.request.remote_addr
        user_agent = flask.request.user_agent.string
        try:
            requests_collection = mongo.db['requests']
            requests_collection.insert_one({
                'key': key,
                'ip_address': ip_address,
                'user_agent': user_agent
            })
        except Exception as e:
            print(e)

        return render_template('quotes.html', tweet=tweet)

    return app
