from telegram.ext import Updater,CommandHandler,MessageHandler,Filters,ConversationHandler,RegexHandler
from telegram import KeyboardButton,ReplyKeyboardMarkup
import logging
from twitter import *
from db import *
import os

''
CHOICE,ADD,REMOVE = range(3)

main_keyboard = [[KeyboardButton('Add sub')],[KeyboardButton('Remove sub')],[KeyboardButton('Send me the tweets')],[KeyboardButton('Stop sending tweets')]]
main_reply_markup = ReplyKeyboardMarkup(main_keyboard,resize_keyboard=True)

def start(bot,update):
    update.message.reply_text('What can i do for you', reply_markup=main_reply_markup)
    return CHOICE

'''we use a blacklist for users who dont want receive tweets'''

def add_to_blacklist(chat_id):
    check = BlackList.objects(chat_id=chat_id).count()
    if check<1:
       user_to_ban = BlackList(chat_id=chat_id)
       user_to_ban.save()

def remove_from_blacklist(chat_id):
    user_to_ban = BlackList.objects(chat_id=chat_id)
    user_to_ban.delete()


def choice(bot,update,user_data):
    if update.message.text == 'Add sub':
        keyboard = [[KeyboardButton('Back')]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        update.message.reply_text('Enter username', reply_markup=reply_markup)
        return ADD

    elif update.message.text == 'Remove sub' :
        subs = Subscriptions.objects(chat_id=str(update.message.chat_id))
        subs_dict={}
        text = 'Your subscriptions:\n'
        keyboard = [[KeyboardButton('Back')]]
        if subs.count() > 0:
            index = 1
            selection_buttons =[]
            for sub in subs:
                subs_dict[str(index)]=sub.twitter_screen_name
                text=text+str(index)+'.'+str(sub.twitter_screen_name)+'\n'
                selection_buttons.append(KeyboardButton(str(index)))
                user_data['subs_dict']=subs_dict
                index = index + 1
            keyboard.append(selection_buttons)
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            update.message.reply_text(text,reply_markup=reply_markup)
            return REMOVE

        else :
            update.message.reply_text('You have no subscriptions', reply_markup=main_reply_markup)
            return CHOICE


    elif update.message.text == 'Send me the tweets':
        remove_from_blacklist(str(update.message.chat_id))
        update.message.reply_text('tweets will be sent realtime!',)
        return CHOICE

    elif update.message.text == 'Stop sending tweets':
         add_to_blacklist(str(update.message.chat_id))
         update.message.reply_text('Sending tweets is canceled')
         return CHOICE

def add(bot,update):
    if update.message.text == 'Back':
        update.message.reply_text('What can i do for you', reply_markup=main_reply_markup)
        return CHOICE
    else :
        twitter = Twitter()
        count = Subscriptions.objects(chat_id = str(update.message.chat_id)).count()
        try:
            input = twitter.getUser(update.message.text)
            check = Subscriptions.objects(chat_id = str(update.message.chat_id),twitter_id=str(input.id)).count()
            if check > 0:
                update.message.reply_text('You have added this username before', reply_markup=main_reply_markup)
            else :
                 '''max count for subs, you can change it to whatever you want'''
                 if count<5 :
                    sub = Subscriptions(chat_id=str(update.message.chat_id), twitter_id=str(input.id),
                                       twitter_screen_name=str(update.message.text))
                    sub.save()
                    update.message.reply_text('User has been added', reply_markup=main_reply_markup)
                 else :
                       update.message.reply_text('You have reached maximum number of subscriptions!', reply_markup=main_reply_markup)

        except tweepy.TweepError as e:
            print(e.reason)
            update.message.reply_text('No such user exists', reply_markup=main_reply_markup)
        return CHOICE

def remove(bot,update,user_data):
    if update.message.text == 'Back':
        update.message.reply_text('What can i do for you', reply_markup=main_reply_markup)
        return CHOICE
    else :
         choice = str(update.message.text)
         subs_dict = user_data['subs_dict']
         if choice in subs_dict:
             Subscriptions.objects(chat_id=str(update.message.chat_id),twitter_screen_name=str(subs_dict[choice])).delete()
             update.message.reply_text(subs_dict[choice]+' has been removed successfully',reply_markup=main_reply_markup)
             return CHOICE
         else :
             update.message.reply_text('Please enter a valid selection')

def exit(bot,update) :
    update.message.reply_text('Your settings have been saved')
    remove_from_blacklist(str(update.message.chat_id))
    return ConversationHandler.END

def update_stream_filter(bot,job):
    global my_twitter_stream
    follow_list = Subscriptions.objects().distinct(field='twitter_id')
    my_twitter_stream.disconnect()
    del my_twitter_stream
    twitter = Twitter()
    my_twitter_stream = twitter.getStream()
    my_twitter_stream.filter(follow=follow_list,async=True)
    print(follow_list)
    print('stream updated')

def start_stream():
    follow_list = Subscriptions.objects().distinct(field='twitter_id')
    print(follow_list)
    twitter = Twitter()
    global my_twitter_stream
    my_twitter_stream = twitter.getStream()
    my_twitter_stream.filter(follow=follow_list,async=True)
    print('stream started')

def main():
    TOKEN = "Your telegram bot token"
    PORT = int(os.environ.get('PORT', '5000'))
    updater = Updater(token=TOKEN)
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level = logging.INFO)
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start',start)],
        states={
            CHOICE :[MessageHandler(Filters.text,choice,pass_user_data=True)],
            ADD : [MessageHandler(Filters.text,add)],
            REMOVE:[MessageHandler(Filters.text,remove,pass_user_data=True)]
        },
        fallbacks=[CommandHandler('exit',exit)]
    )
    dispatcher.add_handler(add_conv_handler)
    connectDB()
    start_stream()
    job = updater.job_queue
    job.run_repeating(callback=update_stream_filter,interval=60*6,first=60*6)
    ''' set the webhook to your own url'''
    updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)
    updater.bot.set_webhook("your app url" + TOKEN)
    updater.idle()

if __name__ == '__main__':
     main()
