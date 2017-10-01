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
from QuinielaScrapper import QuinielaScrapper

reload(sys)
sys.setdefaultencoding('utf8')


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

#### GLOBAL STATUS VARIABLES ####
counter = 1
status_name = "status.json"
admin_id = "132976650"

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
    scrapper = QuinielaScrapper()
    status = read_status()
    journey = scrapper.get_journey(status["journey"])

    matches, results = [], []

    for journey_match in journey:
        matches.append(journey_match["match"])
        results.append(journey_match["result"])

    # DEBUG variable
    #results = ["1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1", "1 - M"]
    return matches, results

def echa_la_puta_quiniela(bot, update):
    global admin_id
    journey_matches, _ = get_journey_matches()
    status = read_status()

    table_mid = """
    \\documentclass{beamer}
    \\usepackage{xcolor}
    \\usepackage[utf8]{inputenc}
    \\usepackage{colortbl}

    \\definecolor{Gray}{gray}{0.85}

    \\begin{document}
    \\begin{frame}
"""

    # Check if is admin
    if str(update.message.from_user.id) != admin_id:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: ¡la puta quiniela solo la puede echar Jorge!.')
        return 

    # Check if state is filling
    if status["state"] != "filling":
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: la puta quiniela se echa después de rellenar columnas, ¡no ahora gilipollas!.')
        return

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

    # Change current state to "playing"
    status = read_status()
    status["state"] = "playing"
    write_status(status)

def jornada(bot, update, args):
    status = read_status()

    # Check if is admin
    if str(update.message.from_user.id) != admin_id:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: solo Jorge puede empezar nueva jornada capullo.')
        return 

    # Check if state is finished
    if status["state"] != "finished":
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: la jornada tiene que haberse terminado para poder ejecutar este comando y comenzar una nueva quiniela.')
        return

    # No journey provided
    if len(args) == 0:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: especifica la jornada.')
        return

    # Check if journey is available
    journey = str(args[0])
    scraper = QuinielaScrapper()
    if not scraper.is_journey_available(journey):
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: no hay quiniela para esa jornada.')
        return

    # Refresh status JSON
    status["journey"] = journey
    status["state"] = "journey_ready"
    status["fills"] = {}
    write_status(status)

    # Retrieve journey matches, and send them
    matches, _ = get_journey_matches()
    msg_str = "Jornada %s:\n" % journey
    for i, match in zip(range(1, 16), matches):
        msg_str += "%d. %s\n" % (i, match)
    bot.send_message(
        chat_id=update.message.chat_id,
        text=msg_str
    )


def editar(bot, update, args):
    journey_matches, _ = get_journey_matches()
    match_num = None
    query = update.callback_query
    status = read_status()
    user = update.message.from_user

    # Check if state is filling
    if status["state"] != "filling":
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: ahora no puedes editar ninguna columna.')
        return

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
    journey_matches, _ = get_journey_matches()

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


def status(bot, update):
    status = read_status()
    users_results = []
    finished_matches = 0

    # Quiniela is yet to be filled by other users
    if status["state"] == "filling":
        msg = "La quiniela aún no se ha echado.\nDe momento la han rellenado:\n"
        for user_id in status["fills"].keys():
            msg += "%s, " % status["fills"][user_id]["nick"]
        msg = msg[:-1]
        msg += "\nRellena tu columna ejecutando: \\start"

        bot.send_message(
            text=msg,
            chat_id=update.message.chat_id,
        )
        return
    # Listening for fillings
    if status["state"] == "journey_ready":
        bot.send_message(
            text="Esperando a columnas rellenas (usa /start). Jornada %s" % str(status["journey"]),
            chat_id=update.message.chat_id,
        )
        return

    journey_matches, results = get_journey_matches()

    # Retrieve the users' guessed matches
    print "Results: %s" % str(results)
    for result in results:
        finished_matches += 1 if result != "" and result != " - " else 0
    for user_id in status["fills"].keys():
        user_nick = status["fills"][user_id]["nick"]
        user_fills = status["fills"][user_id]["fill"]
        ok_guess = 0

        for result, user_fill in zip(results, user_fills):
            if (" - " in result and ok_guess == 14) or " - " not in result:
                ok_guess += 1 if result.lower() == user_fill.lower() else 0

        users_results.append({"nick": user_nick, "ok_guess": ok_guess})

    # Create string message
    status_str = "Aciertos de partidos terminados:\n"
    for user_results in users_results:
        status_str += " -> %s: %d/%d\n" % (user_results["nick"], user_results["ok_guess"], finished_matches)
    if finished_matches == 15:
        status_str += "Jornada terminada."
        status["state"] = "finished"
        write_status(status)

    # Send message
    bot.send_message(
        text=status_str,
        chat_id=update.message.chat_id,
    )


def rellenar(bot, update):
    match_to_fill = None
    ask_more = True
    next_message = ''
    journey_matches, _ = get_journey_matches()
    print "journey_matches=%s" % journey_matches

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
    status = read_status()

    # Check if state is journey_ready
    if status["state"] != "journey_ready" and status["state"] != "filling":
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: ya hay una quiniela en juego, ahora no puedes comenzar otra.')
        return

    journey_matches, _ = get_journey_matches()
    update.message.reply_text(text="1. ➡%s⬅\n" % journey_matches[0],
           reply_markup=reply_markup_keyboard)

    # Update state
    status["state"] = "filling"
    write_status(status)


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

def reset(bot, update, args):
    # Check if is admin
    if str(update.message.from_user.id) != admin_id:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: solo Jorge puede resetear hijo de puta.')
        return

    # Check argument
    if len(args) != 1:
        bot.send_message(
            chat_id=update.message.chat_id,
            text='ERROR: pasa por argumento la jornada desde la que resetear.')
        return     

    # Update status
    status = read_status()
    status["fills"] = {}
    status["state"] = "finished"
    status["journey"] = str(args[0])
    status["state"] = "journey_ready"
    write_status(status)

    bot.send_message(
        chat_id=update.message.chat_id,
        text='Reseteado. Ahora estamos en la jornada 10.')
    return    

    return


def help(bot, update):
    update.message.reply_text("Use /start to test this bot.")


def error(bot, update, error):
    logging.warning('Update "%s" caused error "%s"' % (update, error))


# Create the Updater and pass it your bot's token.
updater = Updater("402086176:AAHgHTqknzeHPWBjPDJYJLdG38CQwFNR6W4")

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CallbackQueryHandler(rellenar))
updater.dispatcher.add_handler(CommandHandler('edit', editar, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('jornada', jornada, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('reset', reset, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('status', status))
updater.dispatcher.add_handler(CommandHandler('echa_la_puta_quiniela',
    echa_la_puta_quiniela))
updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_error_handler(error)

# Start the Bot
updater.start_polling()

# Run the bot until the user presses Ctrl-C or the process receives SIGINT,
# SIGTERM or SIGABRT
updater.idle()
