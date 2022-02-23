#!/usr/bin/env python3

from telegram import utils
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, InlineQueryHandler, CallbackQueryHandler, CallbackContext
from telegram.ext.filters import Filters

from downloader import Downloader

import re

with open('token.txt') as f:
    TOKEN = f.readlines()[0].replace('\n','')

updater    = Updater(TOKEN)         # Fetches updates fro Telegram server
dispatcher = updater.dispatcher     # Filters updates and dispaches callbacks

def ask_type(update: Update, context: CallbackContext):
    button_list = [
        InlineKeyboardButton("YouTube", callback_data='youtube'),
        InlineKeyboardButton("File URL", callback_data='url'),
    ]
    reply_markup = InlineKeyboardMarkup.from_column(button_list)
    update.effective_chat.send_message("Where would you like to fetch the audio from?", reply_markup=reply_markup)
    return 'requested-type'

def ask_link(update: Update, context: CallbackContext):
    if update.callback_query.data == 'youtube':
        update.effective_chat.send_message('Paste the YouTube link.')
        return 'requested-yt-link'
    elif update.callback_query.data == 'url':
        update.effective_chat.send_message('Paste the file URL.')
        return 'requested-file-link'
    else:
        update.effective_chat.send_message('Invalid option.')

def fetch_yt_link(update: Update, context: CallbackContext):
    link = update.effective_message.text
    if 'youtube.com' in link:
        id = re.search('v=([0-9a-zA-Z_\-]{11})', link).group(1)
        d = Downloader(link)
    elif 'youtu.be' in link:
        id = re.search('([0-9a-zA-Z_\-]{11})$', link).group(1)
        d = Downloader(link)
    else:
        # Link is actually a search phrase
        id = ''.join(c if c.isalnum() else '_' for c in link)
        d = Downloader(link, search=True)

    update.effective_chat.send_message("Working...")
    d.get_yt_url()

    if d.error:
        update.effective_chat.send_message("Error: " + d.error)
    else:
        update.effective_chat.send_document(document=d.data, filename=f'{id}.amr')

    return ConversationHandler.END

def fetch_file_link(update: Update, context: CallbackContext):
    update.effective_chat.send_message("Attempting to convert linked file")
    return ConversationHandler.END

dispatcher.add_handler(ConversationHandler(
    entry_points=[
        CommandHandler('get', ask_type)
    ],
    states={
        'requested-type': [CallbackQueryHandler(ask_link)],
        'requested-yt-link': [MessageHandler(Filters.text, fetch_yt_link)],
        'requested-file-link': [MessageHandler(Filters.entity('text_link') | Filters.entity('url'), fetch_file_link)],
    },
    fallbacks=[],
))

updater.start_polling()
updater.idle()
