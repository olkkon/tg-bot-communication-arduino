
import logging
import os
import numpy as np

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from serial_wrapper import *

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Superuser is admin of the bot
superuser = ADD_YOUR_OWN_TG_ID
bot_token = ADD_YOUR_BOT_TOKEN
logged_in = False

# Define a few command handlers. These usually take the two arguments update and context.
def start(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2('Hey\! Look what I can do: /help',
        reply_markup=ForceReply(selective=True),
    )

def help_command(update: Update, _: CallbackContext) -> None:
    if logged_in:
        update.message.reply_text("""As a logged in user you can: \n/logout log out\n/photo request for a photo\n/led control the led""")
    else:
        update.message.reply_text("""Without logging in you can: \n/login log in\n""")
    
def login(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    if logged_in:
        update.message.reply_text('You\'re already in...')
    else:
        if trustedfile_contains_name(user.username):
            logged_in = True
            update.message.reply_text(f'Welcome, {user.first_name}!')
        else:
            update.message.reply_text('Sorry, but your account does not have access to this bot.')
            
def logout(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    if logged_in:
        logged_in = False
        update.message.reply_text('Logged out succesfully.')
    else:
        update.message.reply_text('Try first to log in ;) /login')    
    
def default_text(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('I accept only commands. /help')
    
def default_command(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Unknown command. /help')

def photo(update: Update, _: CallbackContext) -> None:
    global logged_in
    status, desc = verify_login_status(update.effective_user.username)
    
    if status:
        update.message.reply_photo(photo=open('test.png','rb'))
    elif desc == 'expired':
        logged_in = False
        update.message.reply_text('You have been removed from the trusted users list. Logging out..')
    else:
        update.message.reply_text('Only for authorizated users.. /login')
        
def add_trusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    
    # Allow superuser to add person to the trusted list
    if user.id == superuser:
        if not context.args:
            update.message.reply_text('Who shall I add?')
        else:
            to_be_added = context.args[0]
            if trustedfile_contains_name(to_be_added):
                update.message.reply_text('User already on the list.')
            else:
                with open("trusted.txt", "a+") as file_object:
                    file_object.seek(0)
                    file_object.write("\n")
                    file_object.write(to_be_added)
                update.message.reply_text(f'Successfully added @{to_be_added} to the list.')   
    elif logged_in:
        update.message.reply_text('Only administrator have access to this command.')
    else:
        update.message.reply_text('This functionality is not in public use.')
        
def remove_trusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    # Allow superuser to delete trusted person from list
    if user.id == superuser:
        if not context.args:
            update.message.reply_text('Who shall I remove?')
        else:
            to_be_deleted = context.args[0]
            if not trustedfile_contains_name(to_be_deleted):
                update.message.reply_text(f'Username @{to_be_deleted} was not found in the list.')   
            else:
                os.rename('trusted.txt','trusted_old.txt')
                with open('trusted_old.txt') as old, open('trusted.txt', 'w') as new:
                    for line in old:
                        if not to_be_deleted.strip() in line.strip():
                            new.write(line)
                os.remove('trusted_old.txt')
                update.message.reply_text(f'Succesfully removed @{to_be_deleted} from the list.')
    elif logged_in:
        update.message.reply_text('Only administrator have access to this command.')
    else:
        update.message.reply_text('This functionality is not in public use.')  
        
def trusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    if user.id == superuser:
        # List all trusted persons
        trusted_users = np.loadtxt('trusted.txt', dtype=str)
        msg = 'Trusted accounts:\n'
        for person in trusted_users.ravel():
            msg = msg + "@" + person + "\n"
        update.message.reply_text(msg)
    elif logged_in:
        update.message.reply_text('Only administrator have access to this command.')
    else:
        update.message.reply_text('This functionality is not in public use.')
        
def led(update: Update, context: CallbackContext) -> None:
    global logged_in
    status, desc = verify_login_status(update.effective_user.username)
    
    # Allow logged in users to control the external led.
    if status:
        if not context.args:
            update.message.reply_text('Please choose setting on/off/state')
        else:
            setting = context.args[0]
            
            if setting == 'state':
                return_value, desc = get_led_state()
            elif setting == 'on':
                setting = True
                return_value, desc = toggle_led(True)
            elif setting == 'off':
                setting = False
                return_value, desc = toggle_led(False)
            else:
                setting = 'fail'
                
            if setting == 'state':
                if return_value:
                    if desc:
                        update.message.reply_text('Led is on.')
                    else:
                        update.message.reply_text('Led is off.')
                else:
                    update.message.reply_text(f'State could not be obtained, {desc}')
            elif setting == 'fail':
                update.message.reply_text('Unknown setting value. Please choose from on/off/state')
            else:
                if return_value:
                    if setting:
                        update.message.reply_text('Led is on!')
                    else:
                        update.message.reply_text('Led is off!')
                else:
                    update.message.reply_text(f'State could not be changed, {desc}')
    elif desc == 'expired':
        logged_in = False
        update.message.reply_text('You have been removed from the trusted users list. Logging out..')
    else:
        update.message.reply_text('Only for authorizated users.. /login')
    
# A helper methods to do the authentication and file handling
def verify_login_status(user: str):
    if logged_in:
        if trustedfile_contains_name(user):
            return True, None
        else:
            return False, 'Expired'
    else:
        return False, 'NotFound'
        
def trustedfile_contains_name(user: str):
    found = False
    with open('trusted.txt', 'r') as file_in:
            for line in file_in:
                if line.strip() == user.strip():
                    found = True
    return found


def main() -> None:

    # Create the Updater and pass it your bot's token.
    updater = Updater(bot_token)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("login", login))
    dispatcher.add_handler(CommandHandler("logout", logout))
    dispatcher.add_handler(CommandHandler("photo", photo))
    dispatcher.add_handler(CommandHandler("addtrusted", add_trusted))
    dispatcher.add_handler(CommandHandler("removetrusted", remove_trusted))
    dispatcher.add_handler(CommandHandler("deletetrusted", remove_trusted))
    dispatcher.add_handler(CommandHandler("trusted", trusted))
    dispatcher.add_handler(CommandHandler("led", led))
    
    dispatcher.add_handler(MessageHandler(Filters.command, default_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, default_text))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
