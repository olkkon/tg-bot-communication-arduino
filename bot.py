
import logging
import numpy as np
import os

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# Authentication and trusted users
trusted_users = np.loadtxt('trusted.txt', dtype=str)
superuser = YOUR_OWN_TG_ID
logged_in = False


# Define a few command handlers. These usually take the two arguments update and context.
def start(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2('Terve\! Katso mitä osaan tehdä: /help',
        reply_markup=ForceReply(selective=True),
    )

def help_command(update: Update, _: CallbackContext) -> None:
    if logged_in:
        update.message.reply_text("""Sisäänkirjautuneena käyttäjänä voit käyttää seuraavia komentoja: \n/logout kirjaudu ulos\n/photo lähetä kuva\n/help näytä tämä teksti""")
    else:
        update.message.reply_text("""Ilman sisäänkirjautumista voit käyttää seuraavia komentoja: \n/login kirjaudu sisään\n/help näytä tämä teksti""")
    
def login(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    if logged_in:
        update.message.reply_text('Olet jo sisäänkirjautunut!')
    else:
        if user.username in trusted_users:
            logged_in = True
            update.message.reply_text('Sisäänkirjautuminen onnistui!')
        else:
            update.message.reply_text('Et voi kirjautua sisään tunnuksellasi.')
            
def logout(update: Update, _: CallbackContext) -> None:
    user = update.effective_user
    global logged_in
    
    if logged_in:
        logged_in = False
        update.message.reply_text('Uloskirjautuminen onnistui!')
    else:
        update.message.reply_text('Olet jo uloskirjautuneena!')    
    
def Photo(update: Update, _: CallbackContext) -> None:
    if logged_in:
        update.message.reply_photo(photo=open('test.png','rb'))
    else:
        update.message.reply_text('Sinun pitää kirjautua ensin sisään.')
    
def default(update: Update, _: CallbackContext) -> None:
    update.message.reply_text('Hyväksyn vain komentoja. /help')

def Photo(update: Update, _: CallbackContext) -> None:
    if logged_in:
        update.message.reply_photo(photo=open('test.png','rb'))
    else:
        update.message.reply_text('Sinun pitää kirjautua ensin sisään.')
        
def AddTrusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    global trusted_users
    
    if user.id == superuser:
        to_be_added = context.args[0]
        if to_be_added in trusted_users:
            update.message.reply_text('Käyttäjä löytyy jo luotettujen listalta!')
        else:
            # Kirjoitetaan uusi luotettava ID talteen tiedostoon
            with open("trusted.txt", "a+") as file_object:
                file_object.seek(0)
                file_object.write("\n")
                file_object.write(to_be_added)
            trusted_users = np.append(trusted_users, to_be_added)
            update.message.reply_text(f'Lisättiin @{to_be_added} luotettujen listalle.')   
        
    elif logged_in:
        update.message.reply_text('Vain botin ylläpitäjä voi lisätä uusia luotettuja henkilöitä.')
    else:
        update.message.reply_text('Tämä toiminnallisuus ei ole yleisessä käytössä.')
        
def RemoveTrusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    global trusted_users
    
    if user.id == superuser:
        # Poistetaan haluttu ID luettelosta, jos se vain on mahdollista
        to_be_deleted = context.args[0]
        found = False
        
        with open('trusted.txt', 'r') as file_in:
            for line in file_in:
                if line.strip() == to_be_deleted.strip():
                    found = True
            
        if not found:
            update.message.reply_text(f'Käyttäjänimeä @{to_be_deleted} ei löytynyt luotettujen listalta.')   
        else:
            os.rename('trusted.txt','trusted_old.txt')
            with open('trusted_old.txt') as old, open('trusted.txt', 'w') as new:
                for line in old:
                    if not to_be_deleted.strip() in line.strip():
                        new.write(line)
            os.remove('trusted_old.txt')
            trusted_users = np.delete(trusted_users, np.argwhere(trusted_users==to_be_deleted))
            update.message.reply_text(f'Käyttäjänimi @{to_be_deleted} poistettiin luotettujen listalta.')

    elif logged_in:
        update.message.reply_text('Vain botin ylläpitäjä voi poistaa luotettuja henkilöitä.')
    else:
        update.message.reply_text('Tämä toiminnallisuus ei ole yleisessä käytössä.')
        
def Trusted(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    if user.id == superuser:
        # Listataan kaikki luotetut henkilöt
        msg = 'Luotetut henkilöt:\n'
        for person in trusted_users:
            msg = msg + "@" + person + "\n"
        update.message.reply_text(msg)
    elif logged_in:
        update.message.reply_text('Vain botin ylläpitäjä voi tarkastella luotettujen henkilöiden listaa.')
    else:
        update.message.reply_text('Tämä toiminnallisuus ei ole yleisessä käytössä.')

def main() -> None:

    # Create the Updater and pass it your bot's token.
    updater = Updater(ADD_YOUR_BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("login", login))
    dispatcher.add_handler(CommandHandler("logout", logout))
    dispatcher.add_handler(CommandHandler("photo", Photo))
    dispatcher.add_handler(CommandHandler("addtrusted", AddTrusted))
    dispatcher.add_handler(CommandHandler("removetrusted", RemoveTrusted))
    dispatcher.add_handler(CommandHandler("trusted", Trusted))
    
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, default))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
