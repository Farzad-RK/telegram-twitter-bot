import tweepy
from db import *
import telegram

class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        if not hasattr(status, 'retweeted_status'):
               print('incomming status :)')
               print(status.user.screen_name+' : '+status.text)
               bot = telegram.Bot(token='387093650:AAGb4uZjtt71N4LVPn_flI8JKTOWFy_ZW10')
               send_list = Subscriptions.objects(twitter_screen_name=status.user.screen_name)
               print(send_list)
               for user in send_list:
                   check = BlackList.objects(chat_id=str(user.chat_id)).count()
                   if check<1:
                       print(user.chat_id)
                       bot.send_message(chat_id=user.chat_id, text='From @'+status.user.screen_name+' : '+status.text)
    def on_connect(self):
        print('stream connected')

    def on_disconnect(self, notice):
        print('disconnected :)')

    def on_error(self, status_code):
        if status_code == 420:
            # returning False in on_error disconnects the stream
            return False

class Twitter:

    def __init__(self):
        ''' your twitter api access credentials '''
        self.auth = tweepy.OAuthHandler('', '')
        self.auth.set_access_token('',
                              '')
    def getAPI(self):
        api = tweepy.API(self.auth)
        return api

    def getUser(self,name):
        user = self.getAPI().get_user(name)
        return user
    def getStream(self):
        myStreamListener = MyStreamListener()
        myStream = tweepy.Stream(auth=self.getAPI().auth, listener=myStreamListener)
        return myStream
