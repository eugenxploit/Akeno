import random
import time
from time import sleep

from telegram import MessageEntity
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, run_async
from telegram import ParseMode

import Elizabeth.modules.helper_funcs.fun_strings as fun
from Elizabeth import dispatcher
from Elizabeth.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from Elizabeth.modules.sql import afk_sql as sql
from Elizabeth.modules.users import get_user_id
from Elizabeth import REDIS
from Elizabeth.modules.sql.afk_redis import start_afk, end_afk, is_user_afk, afk_reason
from Elizabeth.modules.helper_funcs.readable_time import get_readable_time

AFK_GROUP = 7
AFK_REPLY_GROUP = 8


@run_async
def afk(update, context):
    args = update.effective_message.text.split(None, 1)
    user = update.effective_user
    if not user:  # ignore channels
        return

    if user.id == 777000:
        return
    start_afk_time = time.time()
    if len(args) >= 2:
        reason = args[1]
    else:
        reason = "none"
    start_afk(update.effective_user.id, reason)
    REDIS.set(f'afk_time_{update.effective_user.id}', start_afk_time)
    fname = update.effective_user.first_name
    try:
        update.effective_message.reply_text(
            "{} is now Away!".format(fname))
    except BadRequest:
        pass
    
    #sleep(7)
    #afksend.delete()


@run_async
def no_longer_afk(update, context):
    user = update.effective_user
    message = update.effective_message
    if not user:  # ignore channels
        return

    if not is_user_afk(user.id):  #Check if user is afk or not
        return
    end_afk_time = get_readable_time((time.time() - float(REDIS.get(f'afk_time_{user.id}'))))
    REDIS.delete(f'afk_time_{user.id}')
    res = end_afk(user.id)
    if res:
        if message.new_chat_members:  #dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            message.reply_text(
                "{} is no longer AFK!\nTime you were AFK for: {}".format(firstname, end_afk_time))
        except Exception:
            return
            #sleep(10)
            #unafk.delete()
        except BaseException:
            return


@run_async
def reply_afk(update, context):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION]
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type == MessageEntity.MENTION:
                user_id = get_user_id(
                    message.text[ent.offset: ent.offset + ent.length]
                )
                if not user_id:
                    # Should never happen, since for a user to become AFK they
                    # must have spoken. Maybe changed username?
                    return

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

                try:
                    chat = bot.get_chat(user_id)
                except BadRequest:
                    print(
                        "Error: Could not fetch userid {} for AFK module".format(
                            user_id
                        )
                    )
                    return
                fst_name = chat.first_name

            else:
                return

            check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        check_afk(update, context, user_id, fst_name, userc_id)


def check_afk(update, context, user_id, fst_name, userc_id):
    if is_user_afk(user_id):
        reason = afk_reason(user_id)
        since_afk = get_readable_time((time.time() - float(REDIS.get(f'afk_time_{user_id}'))))
        if reason == "none":
            if int(userc_id) == int(user_id):
                return
            res = "{} is AFK!\n<b>Since:</b> {}".format(fst_name, since_afk, parse_mode="html")
            update.effective_message.reply_text(res)
        else:
            if int(userc_id) == int(user_id):
                return
            res = "{} is AFK!\n<b>Reason:</b>\n{}\n<b>Last seen:</b> {}".format(fst_name, reason, since_afk, parse_mode="html")
            update.effective_message.reply_text(res)
            #sleep(10)
            #replafk.delete()

            
def __user_info__(user_id):
    is_afk = is_user_afk(user_id)
    text = ""
    if is_afk:
        since_afk = get_readable_time((time.time() - float(REDIS.get(f'afk_time_{user_id}'))))
        text = "<i>This user is currently afk (away from keyboard).</i>"
        text += f"\n<i>Since: {since_afk}</i>"
       
    else:
        text = "<i>Currently this user isn't afk (away from keyboard).</i>"
    return text


def __gdpr__(user_id):
    sql.rm_afk(user_id)


AFK_HANDLER = DisableAbleCommandHandler("afk", afk)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex("(?i)brb"), afk, friendly="afk"
)
BYE_REGEX_HANDLER = DisableAbleMessageHandler(
    Filters.regex("(?i)bye"), afk, friendly="afk"
)
NO_AFK_HANDLER = MessageHandler(Filters.all & Filters.group, no_longer_afk)
AFK_REPLY_HANDLER = MessageHandler(
    Filters.all & Filters.group & ~Filters.update.edited_message, reply_afk
)


dispatcher.add_handler(AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(BYE_REGEX_HANDLER, AFK_GROUP)
dispatcher.add_handler(NO_AFK_HANDLER, AFK_GROUP)
dispatcher.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)


__mod_name__ = "AFK"

__help__ = """
⚙️ Away from keyboard
 
 • /afk <reason>: Mark yourself as AFK.
 • brb <reason>: Same as the afk command - but not a command.
"""
__command_list__ = ["afk"]
__handlers__ = [
    (AFK_HANDLER, AFK_GROUP),
    (AFK_REGEX_HANDLER, AFK_GROUP),
    (NO_AFK_HANDLER, AFK_GROUP),
    (AFK_REPLY_HANDLER, AFK_REPLY_GROUP),
    (BYE_REGEX_HANDLER, AFK_GROUP),
]
