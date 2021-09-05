import ipdb
import os
import logging
from dotenv import load_dotenv
# telegram library
from telegram import ParseMode
from telegram import Update
from telegram.ext import Updater, PicklePersistence, CommandHandler, CallbackContext
# custom functions
from functions.logging import set_up_logging
from functions.translations import translate, set_chat_language, get_lang
from functions.parser import parse_roll, evaluate_roll, InfinityRolls

load_dotenv()

TOKEN = os.getenv("TOKEN")

# Enable logging
logger = set_up_logging(logging.DEBUG)

# Make the bot persistent
my_persistence = PicklePersistence(filename='rolldice-persistence.ptb')

# Multilanguage
_ = translate


def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    if 'lang' not in context.chat_data.keys():
        set_chat_language(update, context)
    if 'usage' not in context.bot_data.keys():
        context.bot_data['usage'] = 0
    lang = get_lang(context)
    update.message.reply_text(_('start', lang))
    # logging
    logger.debug(f'Chat {update.effective_chat.id} - Start')
    return


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    lang = get_lang(context)
    update.message.reply_text(_("help", lang))
    # logging
    logger.debug(f'Chat {update.effective_chat.id} - Help')
    return


def roll(update: Update, context: CallbackContext) -> None:
    lang = get_lang(context)
    context.bot_data['usage'] += 1
    # get command
    command = ' '.join(context.args)
    try:
        result, res_str, description = parse_roll(command)
    except InfinityRolls:
        update.message.reply_text(_("infinity", lang), reply_to_message_id=update.message.message_id)
        logger.warning(f'Chat {update.effective_chat.id} - InfinityRolls due to {command}')
        return
    except ValueError:
        update.message.reply_text(_("bad_format", lang), reply_to_message_id=update.message.message_id)
        logger.warning(f'Chat {update.effective_chat.id} - ValueError due to: {command}')
        return
    except Exception:
        update.message.reply_text(_("error", lang), reply_to_message_id=update.message.message_id)
        logger.error(f'Chat {update.effective_chat.id} - Error due to: {command}')
        return
    subresults = res_str
    if subresults[0] == "+":
        subresults = subresults[1:]
    if description:
        dice_command = command[:-len(description)]
        result_string = f"<b>{result}</b> -> {description}"
    else:
        dice_command = command
        result_string = f"<b>{result}</b>"
    name = update.message.from_user.first_name
    update.message.reply_text(_("roll", lang).format(
        name, dice_command, subresults, result_string
        ), reply_to_message_id=update.message.message_id, parse_mode=ParseMode.HTML)


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, persistence=my_persistence)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("roll", roll))
    # Start the Bot
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
