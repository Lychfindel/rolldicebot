import os
from pathlib import Path
import yaml
from telegram import Update
from telegram.ext import CallbackContext

LANGUAGE_IT = 'it'
LANGUAGE_EN = 'en'
DEFAULT_LANG = LANGUAGE_EN

# Languages
localedir = Path(__file__).parent.parent / 'locale'
# localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
LOCALES = {
    LANGUAGE_IT: {
        "name": "italiano",
        "code": "it",
        "symbol": "\U0001F1EE\U0001F1F9",
        "file": "rolldice_bot-it.yaml",
    },
    LANGUAGE_EN: {
        "name": "english",
        "code": "en",
        "symbol": "\U0001F1EC\U0001F1E7",
        "file": "rolldice_bot-en.yaml",
    }
}
for lang in LOCALES.keys():
    with open(os.path.join(localedir, LOCALES[lang]["file"])) as stream:
        LOCALES[lang]["text"] = yaml.load(stream, Loader=yaml.FullLoader)


def translate(string, lang=DEFAULT_LANG):
    """Translate a string in the required language"""
    # If the requested language is not available use the default one
    if lang not in LOCALES.keys():
        lang = DEFAULT_LANG

    # Check if the string is present in the current language
    if string in LOCALES[lang]["text"].keys():
        translation = LOCALES[lang]["text"][string]
    # Otherwise look for the string in the default language
    elif (lang != DEFAULT_LANG) and (string in LOCALES[DEFAULT_LANG]["text"].keys()):
        translation = LOCALES[DEFAULT_LANG]["text"][string]
    # Worst case: we use the input as output
    else:
        translation = string

    return translation


def set_chat_language(update: Update, context: CallbackContext, language=None) -> None:
    """
    Set the language of a chat
    """
    if not language:
        language = update.effective_user.language_code

    if language in LOCALES.keys():
        selected_language = language
    else:
        selected_language = DEFAULT_LANG

    context.chat_data['lang'] = selected_language
    return


def get_lang(context: CallbackContext) -> str:
    """
    Get the current language
    """
    return context.chat_data.get('lang', DEFAULT_LANG)
