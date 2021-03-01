import html
import random
import time

from telegram import ParseMode, Update, ChatPermissions
from telegram.ext import CallbackContext, run_async, Filters, MessageHandler
from telegram.error import BadRequest

from Elizabeth import dispatcher
from Elizabeth.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from Elizabeth.modules.helper_funcs.chat_status import (is_user_admin)
from Elizabeth.modules.helper_funcs.extraction import extract_user

ARAGIFS = [
         'CgACAgUAAx0CTCs8lgABAg1KX6e6iLkD3UVmuqDXJKWg8C1dljwAArgBAAK0pThVvwOSjYhlMsQeBA',
         'CgACAgUAAx0CTCs8lgABAg8eX6fCo-C_5jepnqtlEljgbNuXbnsAAtABAAL8LUFVgFSPB8jG874eBA',
          'CgACAgUAAx0CTCs8lgABAhAXX6fIxIEa1yx5BrOkmuqggwAB0ePMAAL-AQACCXk5Vc8MzDnCRP7xHgQ'
]


@run_async
def ara(update: Update, context: CallbackContext):
    message = update.effective_message
    name = message.reply_to_message.from_user.first_name if message.reply_to_message else message.from_user.first_name
    reply_animation = message.reply_to_message.reply_animation if message.reply_to_message else message.reply_animation
    reply_animation(
        random.choice(fun_strings.ARAGIFS), caption=f'Ara Ara! {name}')
    
    
    
    
ARA_HANDLER = DisableAbleCommandHandler("ara", ara)
ARA_REGEX_HANDLER = DisableAbleMessageHandler(Filters.regex(r"^Ara(.*)$"), ara, friendly="ara")
