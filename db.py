from mongoengine import *

'''Use your mongodb credentials to connect to DB.I created a db at mlab 
   and it works well. 
'''
def connectDB():
    connect(db='DB name',host='DB host')

class Subscriptions(Document):
      chat_id = StringField(max_length=150)
      twitter_id = StringField(max_length=150)
      twitter_screen_name = StringField(max_length=150)

class BlackList(Document):
      chat_id = StringField(max_length=150)
