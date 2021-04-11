
import logging
import numpy as np
import os

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from serial_wrapper import send_boolean_to_arduino

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Superuser is admin of the bot
superuser = ADD_YOUR_OWN_TG_ID
bot_token = ADD_YOUR_BOT_TOKEN
logged_in = False

# Return value constants for the login verification
LOGIN_FOUND     = 0
LOGIN_NOT_FOUND = 1
LOGIN_EXPIRED   = 2

# Define a few command handlers. These usually take the two arguments update and context.
def start(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2('Terve\! Katso mitä osaan tehdä: /help',
        reply_markup=ForceReply(selective=True),
    )

def help_command(update: Update, _: CallbackContext) -> None:
    if logged_in:
        update.message.reply_text("""Sisäänkirjautuneena käyttäjänä voit käyttää seuraavia komentoja: \n/logout kirjaudu ulos\n/photo lähetä kuva\n/help näytä tämä teksti\n/led ohjaa arduinoon liitettyä lediä""")
    else:
        update.message.reply_text("""Ilman sisäänkirjautumista voit käyttää seuraavia komentoja: \n/login kirjaudu sisään\n/help näytä tämä teksti""")
    
def login(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    if logged_in:
        update.message.reply_text('Olet jo sisällä...')
    else:
        if trustedfile_contains_name(user.username):
            logged_in = True
            update.message.reply_text(f'Tervetuloa, {user.first_name}!')
        else:
            update.message.reply_text('Sori, tunnuksellasi ei ole pääsyä tälle botille.')
            
def logout(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    if logged_in:
        logged_in = False
        update.message.reply_text('Uloskirjautuminen onnistui.')
    else:
        update.message.reply_text('Yritä ensin kirjautua sisään ;) /login')    
    
def default_text(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Hyväksyn vain komentoja. /help')
    
def default_command(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Tuntematon komento. /help')

def photo(update: Update, _: CallbackContext) -> None:
    global logged_in
    status = verify_login_status(update.effective_user.username)
    
    if status == LOGIN_FOUND:
        update.message.reply_photo(photo=open('test.png','rb'))
    elif status == LOGIN_EXPIRED:
        logged_in = False
        update.message.reply_text('Sinut on poistettu luotettujen listalta. Kirjaudutaan ulos..')
    else:
        update.message.reply_text('Vain sisäänkirjautuneille.. /login')
        
def add_trusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    
    # Allow superuser to add person to the trusted list
    if user.id == superuser:
        if not context.args:
            update.message.reply_text('Kenet pitäisi lisätä?')
        else:
            to_be_added = context.args[0]
            if trustedfile_contains_name(to_be_added):
                update.message.reply_text('Käyttäjä löytyy jo listalta.')
            else:
                with open("trusted.txt", "a+") as file_object:
                    file_object.seek(0)
                    file_object.write("\n")
                    file_object.write(to_be_added)
                update.message.reply_text(f'Lisättiin @{to_be_added} listalle.')   
    elif logged_in:
        update.message.reply_text('Vain ylläpitäjällä on oikeus tähän komentoon.')
    else:
        update.message.reply_text('Tämä toiminnallisuus ei ole yleisessä käytössä.')
        
def remove_trusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    # Allow superuser to delete trusted person from list
    if user.id == superuser:
        if not context.args:
            update.message.reply_text('Kenet pitäisi poistaa?')
        else:
            to_be_deleted = context.args[0]
            if not trustedfile_contains_name(to_be_deleted):
                update.message.reply_text(f'Käyttäjänimeä @{to_be_deleted} ei löytynyt listalta.')   
            else:
                os.rename('trusted.txt','trusted_old.txt')
                with open('trusted_old.txt') as old, open('trusted.txt', 'w') as new:
                    for line in old:
                        if not to_be_deleted.strip() in line.strip():
                            new.write(line)
                os.remove('trusted_old.txt')
                update.message.reply_text(f'Käyttäjänimi @{to_be_deleted} poistettiin listalta.')
    elif logged_in:
        update.message.reply_text('Vain ylläpitäjällä on oikeus tähän komentoon.')
    else:
        update.message.reply_text('Tämä toiminnallisuus ei ole yleisessä käytössä.')    
        
   
        
def trusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    if user.id == superuser:
        # List all trusted persons
        trusted_users = np.loadtxt('trusted.txt', dtype=str)
        msg = 'Luotetut henkilöt:\n'
        for person in trusted_users.ravel():
            msg = msg + "@" + person + "\n"
        update.message.reply_text(msg)
    elif logged_in:
        update.message.reply_text('Vain ylläpitäjällä on oikeus tähän komentoon.')
    else:
        update.message.reply_text('Tämä toiminnallisuus ei ole yleisessä käytössä.')
        
def led(update: Update, context: CallbackContext) -> None:
    global logged_in
    status = verify_login_status(update.effective_user.username)
    
    # Allow logged in users to control the external led
    if status == LOGIN_FOUND:
        if not context.args:
            update.message.reply_text('Muista valita asetusvaihtoehto on/off')
        else:
            setting = context.args[0]
            if setting == 'on':
                setting = True
            elif setting == 'off':
                setting = False
                
            return_value, desc = send_boolean_to_arduino(setting)    
            if return_value:
                if setting:
                    update.message.reply_text('Ledi päällä!')
                else:
                    update.message.reply_text('Ledi pois päältä!')
            else:
                update.message.reply_text(f'Asetusta ei voitu muuttaa. Virhe: {desc}')
    elif status == LOGIN_EXPIRED:
        logged_in = False
        update.message.reply_text('Sinut on poistettu luotettujen listalta. Kirjaudutaan ulos..')
    else:
        update.message.reply_text('Vain sisäänkirjautuneille.. /login')
    
        
def verify_login_status(user: str):
    if logged_in:
        if trustedfile_contains_name(user):
            return LOGIN_FOUND
        else:
            return LOGIN_EXPIRED
    else:
        return LOGIN_NOT_FOUND
        
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
    
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, default_text))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
