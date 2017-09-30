#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Basic example for a bot that uses inline keyboards.
# This program is dedicated to the public domain under the CC0 license.

import sys
import os
import json
import logging
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

reload(sys)
sys.setdefaultencoding('utf8')


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

#### GLOBAL STATUS VARIABLES ####
counter = 1
status_name = "status.json"


#### KEYBOARDS ####
keyboard = [[InlineKeyboardButton("1", callback_data='1'),
             InlineKeyboardButton("X", callback_data='x'),
            InlineKeyboardButton("2", callback_data='2')]]
reply_markup_keyboard = InlineKeyboardMarkup(keyboard)

keyboard_pleno = [[InlineKeyboardButton("0", callback_data='pleno-0'),
             InlineKeyboardButton("1", callback_data='pleno-1'),
             InlineKeyboardButton("2", callback_data='pleno-2'),
            InlineKeyboardButton("M", callback_data='pleno-M')]]
reply_markup_keyboard_pleno = InlineKeyboardMarkup(keyboard_pleno)

keyboard_edit = [[InlineKeyboardButton("1", callback_data='edit-1'),
             InlineKeyboardButton("X", callback_data='edit-x'),
            InlineKeyboardButton("2", callback_data='edit-2')]]
reply_markup_keyboard_edit = InlineKeyboardMarkup(keyboard_edit)


partidos = ["Deportivo - Getafe ",  "Sevilla - Málaga ",  "Levante - Alavés ",
        "Leganés - At. Madrid ",  "R. Sociedad - Betis ",  "Barcelona - Las Palmas ",
        "Valencia - Athletic Club ",  "Villarreal - Eibar ",  "Real Madrid - Espanyol ",
        "Lorca FC - Cádiz ",  "Alcorcón - Granada ",
        "Huesca - Rayo Vallecano ",  "Osasuna - Sporting ",  "Lugo - Tenerife", 
        "At. Madrid Femenino - Athletic Femenino"]



def read_status():
    f = open(status_name)
    return json.load(f)


def write_status(status):
    f = open(status_name, 'w')
    json.dump(status, f)

def get_journey_matches():
    global partidos
    return partidos

def echa_la_puta_quiniela(bot, update):
    journey_matches = get_journey_matches()
    status = read_status()

    table_mid = """
    \\documentclass{beamer}
    \\usepackage{xcolor}
    \\usepackage{colortbl}

    \\definecolor{Gray}{gray}{0.85}

    \\begin{document}
    \\begin{frame}
"""

    # Table header
    table_mid += "\\begin{tabular}{ |>{\columncolor{Gray}} c | >{\columncolor{Gray}}r |"
    users = " & "
    for key in status["fills"].keys():
        table_mid += " c |"
        users += "& " + status["fills"][key]["nick"]
    table_mid += " }\n\\hline\n"
    users += "\\\\\n\\hline\n"
    table_mid += users

    # Fill matches
    for match in range(15):
        match_line = str(match + 1) + ". & " + journey_matches[match]
        for user in status["fills"].keys():
            match_line += " & " + status["fills"][user]["fill"][match]
        match_line += "\\\\\n\\hline\n"
        table_mid += match_line

    # Fill tail
    table_mid += """
        \\end{tabular}
        \\end{frame}
        \\end{document}
    """

    # Write LaTeX
    f = open('tmp_table.tex', 'w')
    f.write(table_mid)
    f.close()

    # Compile and convert to image
    os.system("pdflatex tmp_table.tex")
    os.system("convert -density 300 -trim tmp_table.pdf -quality 100 tmp_table.png")
    bot.send_photo(chat_id=update.message.chat_id, photo=open('tmp_table.png', 'rb'))

def editar(bot, update, args):
    journey_matches = get_journey_matches()
    match_num = None
    query = update.callback_query
    status = read_status()
    user = update.message.from_user

    # No match provided
    if len(args) == 0:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: especifica el número del partido a\
 editar.')
        return

    # User has not filled his column yet
    if str(user.id) not in status["fills"]:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: aún no has hecho tu columna. Ejecuta \\start antes.')
        return

    try:
        match_num = int(args[0])
    except ValueError, IndexError:
        pass

    if match_num and match_num >= 1 and match_num <= 14:
        bot.send_message(
            text=journey_matches[match_num-1],
            chat_id=update.message.chat_id,
            message_id=update.message.message_id,
            reply_markup=reply_markup_keyboard_edit)
        status["fills"][str(user.id)]["editing"] = match_num
        write_status(status)
    else:
        update.message.reply_text(text='ERROR: hay que poner un número del 1 al 14.')


def editar_partido(bot, update):
    journey_matches = get_journey_matches()

    query = update.callback_query
    fill_answer = query.data
    new_result = fill_answer.replace('edit-', '')
    status = read_status()
    user = query.from_user

    # Edit the value
    edit_match = status["fills"][str(user.id)]["editing"]
    status["fills"][str(user.id)]["fill"][edit_match - 1] = new_result
    write_status(status)

    # Confirm message
    confirm_message = 'Así queda tu columna %s:\n' % user.first_name
    filled_num = len(status["fills"][str(user.id)]["fill"])
    for match in range(filled_num):
        filled_value = status["fills"][str(user.id)]["fill"][match]
        confirm_message += "%d. %s: %s\n" % (match + 1, journey_matches[match], filled_value)

    bot.edit_message_text(
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        text=confirm_message)


def rellenar(bot, update):
    match_to_fill = None
    ask_more = True
    next_message = ''
    journey_matches = get_journey_matches()

    query = update.callback_query
    fill_answer = query.data
    status = read_status()
    print '\n\n------------------------------------------------------------------------'
    print "STATUS: %s" % str(status)
    user = query.from_user

    # Check if it is an edit operation
    if "edit-" in fill_answer:
        editar_partido(bot, update)
        return

    # Detect if we are in a pre-fill situation
    print "FILL_ANSWER: " + str(fill_answer)
    pleno_pre_fill = None
    pre_fill_value = None
    pleno_answer = fill_answer == "pleno-0" or fill_answer == "pleno-1"\
            or fill_answer == "pleno-2" or fill_answer == "pleno-M"
    fill_answer = fill_answer.replace('pleno-', '')
    print 'PLENO_ANSWER: ' + str(pleno_answer)
    if str(user.id) in status["fills"]:
        if "prefill" not in status["fills"][str(user.id)] and pleno_answer:
            status["fills"][str(user.id)]["prefill"] = fill_answer
            pleno_pre_fill = fill_answer
        elif "prefill" in status["fills"][str(user.id)] and pleno_answer:
            pre_fill_value = status["fills"][str(user.id)]["prefill"]
            del status["fills"][str(user.id)]["prefill"]

    # Fill answered match
    print 'PLENO_PRE_FILL: ' + str(pleno_pre_fill)
    if not pleno_pre_fill:
        if str(user.id) not in status["fills"]:
            status["fills"][str(user.id)] = {"nick": user.first_name,
                    "fill": [fill_answer]}
        elif not pre_fill_value:
            status["fills"][str(user.id)]["fill"].append(fill_answer)
        else:
            status["fills"][str(user.id)]["fill"].append(
                    pre_fill_value + " - " + fill_answer)
    print "STATUS-pre-write: %s\n" % str(status)
    write_status(status)

    # Create next matches to be asked (or finish message)
    filled_num = len(status["fills"][str(user.id)]["fill"])
    print 'FILLED_NUM: ' + str(filled_num)
    for match in range(filled_num):
        filled_value = status["fills"][str(user.id)]["fill"][match]
        next_message += "%d. %s: %s\n" % (match + 1, journey_matches[match], filled_value)
    if filled_num == 14 and pleno_pre_fill:
        next_message += "➡%s: %s⬅\n" % (journey_matches[filled_num],
                pleno_pre_fill)
    elif filled_num < 15:
        next_message += "➡%s⬅\n" % journey_matches[filled_num]

    # Ask to fill more, or display filled matches
    if filled_num == 15:
        bot.edit_message_text(
            text="así queda tu columna %s:\n%s" % (user.first_name,
                next_message),
            chat_id=query.message.chat_id,
            message_id=query.message.message_id)
    elif filled_num == 14:
        bot.edit_message_text(
            text=next_message,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup_keyboard_pleno)
    else:
        bot.edit_message_text(
            text=next_message,
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup_keyboard)


def start(bot, update):
    journey_matches = get_journey_matches()
    update.message.reply_text(text="1. ➡%s⬅\n" % journey_matches[0],
           reply_markup=reply_markup_keyboard)


def button(bot, update):
    query = update.callback_query

    keyboard = [[InlineKeyboardButton("1", callback_data='1'),
                 InlineKeyboardButton("X", callback_data='X'),
                InlineKeyboardButton("2", callback_data='2')]]
    global counter

    reply_markup = InlineKeyboardMarkup(keyboard)

    # bot.reply_text('ASA - Getafe:', reply_markup=reply_markup)
    global counter
    counter += 1
    bot.edit_message_text(text="ASA - BASA" + str(counter), chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=reply_markup)
    # bot.edit_message_text(text="Selected option: %s" % query.data,
    #                       chat_id=query.message.chat_id,
    #                       message_id=query.message.message_id)


def help(bot, update):
    update.message.reply_text("Use /start to test this bot.")


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))


# Create the Updater and pass it your bot's token.
updater = Updater("402086176:AAHgHTqknzeHPWBjPDJYJLdG38CQwFNR6W4")

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CallbackQueryHandler(rellenar))
updater.dispatcher.add_handler(CommandHandler('edit', editar, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('echa_la_puta_quiniela',
    echa_la_puta_quiniela))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_error_handler(error)

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()
