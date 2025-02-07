import importlib
import traceback
import html
import json
import re
import time
from typing import Optional
import os
from telegram import Message, Chat, User
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler
from telegram.ext.dispatcher import run_async, DispatcherHandlerStop
from telegram.utils.helpers import escape_markdown
import subprocess
import Elizabeth.modules.sql.users_sql as sql
from Elizabeth.modules.helper_funcs.readable_time import get_readable_time


from Elizabeth import (
    dispatcher,
    DEV_USERS,
    SUDO_USERS,
    SUPPORT_USERS,
    updater,
    TOKEN,
    MESSAGE_DUMP,
    WEBHOOK,
    CERT_PATH,
    PORT,
    URL,
    LOGGER,
    OWNER_ID,
    BLACKLIST_CHATS,
    WHITELIST_CHATS,
    nyaa,
    client,
    StartTime,
    since_time_start,

)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from Elizabeth.modules import ALL_MODULES
from Elizabeth.modules.purge import client
from Elizabeth.modules.helper_funcs.chat_status import is_user_admin
from Elizabeth.modules.helper_funcs.filters import CustomFilters
from Elizabeth.modules.helper_funcs.misc import paginate_modules
from Elizabeth.modules.helper_funcs.alternate import typing_action


PM_START_TEXT = """
——— 「 *Akeno Himejima* 」 ———
[ㅤ](https://telegra.ph/file/204c34acf90114464888a.mp4)
• *A multi-featured chat management bot* 
• *Server Uptime :* `{}`
• *Version :* `2.0.1`
• `{}` *users, across* `{}` *chats.*

• *Welcome user ({}), type /help to get list of my commands.* 
"""
NISSHOKU = "CAACAgQAAxkBAAOsYB7JNWt0STBz_h3MLXNZoN1MmOIAAjcAA9ZzixMWeG5RxOrEiR4E"
AKENOPINGIMG = "https://telegra.ph/file/6cd255ca75a70c4ebe92d.gif"
AKENOPINGIMGTEXT = "*Ara Ara!*\n*Uptime:* `{}`"

buttons = [[InlineKeyboardButton(text="➕ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ",
                                  url="t.me/EchidnaRoBot?startgroup=true"),
]]

buttons += [[InlineKeyboardButton(text="Aʙᴏᴜᴛ",
                                 callback_data="nisshokuabout_"),
             InlineKeyboardButton(text="Sᴜᴘᴘᴏʀᴛ",
                                  url="t.me/akenosupportbot"),
]]

buttons += [[InlineKeyboardButton(text="Hᴇʟᴘ & Cᴏᴍᴍᴀɴᴅs Mᴇɴᴜ",
                                  callback_data="help_back"),
]]

buttons += [[InlineKeyboardButton(text="Cʟᴏsᴇ Mᴇɴᴜ 🔒",
                                  callback_data="close_menu")]]


HELP_STRINGS = f"""
*Aᴋᴇɴᴏ Hɪᴍᴇᴊɪᴍᴀ 〔Bᴇᴛᴀ Rᴇʟᴇᴀsᴇ〕*

• *Basic Sysinfo:*
- _Telethon version:_ `1.16.4`
- _Pyrogram version:_ `1.0.7`
- _Python version:_ `3.8.6`
- _Library version:_ `12.8`
- _SpamWatch API:_ `0.3.0`

• All commands can either be used with / or ! or ?
[ㅤ](https://telegra.ph/file/5d60dd64f29b8cfd03f94.mp4)  
• *For support:* @AkenoSupportBot

"""


IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
USER_BOOK = []
DATA_IMPORT = []
DATA_EXPORT = []

CHAT_SETTINGS = {}
USER_SETTINGS = {}

GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module(
        "Elizabeth.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if not imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception(
            "Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)
        
    if hasattr(imported_module, "__user_book__"):
        USER_BOOK.append(imported_module)    

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard)


@run_async
def test(update, context):
    try:
        print(update)
    except BaseException:
        pass
    update.effective_message.reply_text(
        "UwU tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN
    )
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
@typing_action
def start(update, context):
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        args = context.args
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id,
                                  False)
                else:
                    send_settings(match.group(1), update.effective_user.id,
                                  True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
                #update.effective_message.reply_sticker(NISSHOKU)
                first_name = update.effective_user.first_name
                update.effective_message.reply_text(
                PM_START_TEXT.format(escape_markdown(uptime), sql.num_users(), sql.num_chats(), escape_markdown(first_name)),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
            )
            
    else:
        update.effective_message.reply_video(AKENOPINGIMG, 
                    caption=AKENOPINGIMGTEXT.format(escape_markdown(uptime)), parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                  [
                    InlineKeyboardButton(text="🧭 Ping ", callback_data="start_ping")
                  ],
                
                ]),
            )

def start_p(update, context):
    query = update.callback_query
    if query.data == "start_ping":
        shoko_rbot = get_readable_time((time.time() - since_time_start))
        context.bot.answer_callback_query(query.id,
                                          text=f"Akeno is running since: {shoko_rbot}"
                                               f"\n\nTelegram ping: {ping()}",
                                          show_alert=True, parse_mode=ParseMode.MARKDOWN)    

        
def ping(server='google.com', count=1, wait_sec=1):
   
    cmd = "ping -c {} -W {} {}".format(count, wait_sec, server).split(' ')
    try:
        output = subprocess.check_output(cmd).decode().strip()
        lines = output.split("\n")
        total = lines[-2].split(',')[3].split()[1]
        loss = lines[-2].split(',')[2].split()[0]
        timing = lines[-1].split()[3].split('/')
        ping_t = f"\nmin: {timing[0]}" \
                 f"\navg: {timing[1]}" \
                 f"\nmax: {timing[2]}" \
                 f"\ntotal: {total}" \
                 f"\nloss: {loss}" 
                 
                 
        return ping_t
   
    except Exception as e:
        print(e)
        return None        
        
def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)
        
        
def send_start(update, context):
    uptime = get_readable_time((time.time() - StartTime))

    # Try to remove old message
    
    try:
        query = update.callback_query
        query.message.delete()
    except BaseException:
        pass

    chat = update.effective_chat  # type: Optional[Chat]
    first_name = update.effective_user.first_name
    text = PM_START_TEXT.format(escape_markdown(uptime), sql.num_users(), sql.num_chats(), escape_markdown(first_name)),
    buttons = [[InlineKeyboardButton(text="Hᴇʟᴘ & Cᴏᴍᴍᴀɴᴅs Mᴇɴᴜ ❓",
                                  callback_data="help_back"),
    ]]
             

    buttons += [[InlineKeyboardButton(text="Cʟᴏsᴇ Mᴇɴᴜ 🔒",
                                  callback_data="close_menu")]]


    update.effective_message.reply_text(
        PM_START_TEXT.format(escape_markdown(uptime), sql.num_users(), sql.num_chats(), escape_markdown(first_name)),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
        timeout=60,
        disable_web_page_preview=False,
    )


def start_stop(update, context):
    # Try to remove old message
    try:
        query = update.callback_query
        query.message.delete()
    except BaseException:
        pass

    chat = update.effective_chat  # type: Optional[Chat]
    first_name = update.effective_user.first_name
    text = "Tʜᴇ Mᴇɴᴜ Is Cʟᴏsᴇᴅ 🔒"
    buttons = [[InlineKeyboardButton(text="Rᴇᴏᴘᴇɴ Mᴇɴᴜ 🔓",
                                     callback_data="bot_start")]]

    update.effective_message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
        timeout=60,
        disable_web_page_preview=False,
    )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if
    # something breaks.
    LOGGER.error(msg="Exception while handling an update:",
                 exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them
    # together.
    tb_list = traceback.format_exception(None, context.error,
                                         context.error.__traceback__)
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what
    # happened.
    message = ("An exception was raised while handling an update\n"
               "<pre>update = {}</pre>\n\n"
               "<pre>{}</pre>").format(
                   html.escape(
                       json.dumps(update.to_dict(),
                                  indent=2,
                                  ensure_ascii=False)),
                   html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID,
                             text=message,
                             parse_mode=ParseMode.HTML)


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    try:
        if mod_match:
            module = mod_match.group(1)
            text = ("Here is the help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__) + HELPABLE[module].__help__)
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="🔘  Back  🔘",
                                         callback_data="help_back")
                ]]),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")),
            )

        # ensure no spinny white circle
        #   query.message.delete()
        context.bot.answer_callback_query(query.id)
    except Exception as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            query.message.edit_text(excp.message)
            LOGGER.exception("Exception in help buttons. %s", str(query.data))


@run_async
@typing_action
def get_help(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:

        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Help",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back")]]
            ),
        )

    else:
        keyb = paginate_modules(0, HELPABLE, "help")
        # Add aditional button if staff user detected
        if user.id in DEV_USERS or user.id in SUDO_USERS or user.id in SUPPORT_USERS:
            keyb += [[InlineKeyboardButton(text="Staff",
                                           callback_data="help_staff")]]

        send_help(chat.id, HELP_STRINGS, InlineKeyboardMarkup(keyb))


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def settings_button(update, context):
    query = update.callback_query
    user = update.effective_user
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = context.bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = context.bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(
                    chat.title), reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id)), )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = context.bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(
                    chat.title), reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id)), )

        elif back_match:
            chat_id = back_match.group(1)
            chat = context.bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(
                    escape_markdown(
                        chat.title)), parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        0, CHAT_SETTINGS, "stngs", chat=chat_id)), )

        # ensure no spinny white circle
        query.message.delete()
        context.bot.answer_callback_query(query.id)
    except Exception as excp:
        if excp.message == "Message is not modified":
            pass
        elif excp.message == "Query_id_invalid":
            pass
        elif excp.message == "Message can't be deleted":
            pass
        else:
            query.message.edit_text(excp.message)
            LOGGER.exception(
                "Exception in settings buttons. %s", str(
                    query.data))

@run_async
def Nisshoku_about_callback(update, context):
    query = update.callback_query
    if query.data == "nisshokuabout_":
        query.message.edit_text(
            text="""*About :*
                 \nAkeno is a fork of *Marie + Userindo.* It also includes some unofficial plugins.                 
                 \n-For support, reach out: @AkenoSupportBot
                 \n*Some Anime related links:*
                 \n*Anime Chat:* @AnimeRyuzoku
                 \n*Anime Bot:* @Any_AnimeBot
                 \n*Anime Memes:* @AnimeMemesXD
                 \n\n\n*Ryuzoku* - @Ryuzoku""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Back", callback_data="nisshokuabout_back")
                 ]
                ]
            ),
        )
    elif query.data == "nisshokuabout_back":
        query.message.edit_text(
                PM_START_TEXT,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=True,
        )
                                                                            
@run_async
@typing_action
def get_settings(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    msg.text.split(None, 1)

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


def migrate_chats(update, context):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def is_chat_allowed(update, context):
    if len(WHITELIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id not in WHITELIST_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Unallowed chat! Leaving...")
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    if len(BLACKLIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BLACKLIST_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id,
                text="Unallowed chat! Leaving...")
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    if len(WHITELIST_CHATS) != 0 and len(BLACKLIST_CHATS) != 0:
        chat_id = update.effective_message.chat_id
        if chat_id in BLACKLIST_CHATS:
            context.bot.send_message(
                chat_id=update.message.chat_id, text="Unallowed chat, leaving"
            )
            try:
                context.bot.leave_chat(chat_id)
            finally:
                raise DispatcherHandlerStop
    else:
        pass


def main():
    # test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start, pass_args=True)
    start_p_handler = CallbackQueryHandler(start_p, pattern=r"start_")
    
    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_")
    start_callback_handler = CallbackQueryHandler(
        send_start, pattern=r"bot_start")
    dispatcher.add_handler(start_callback_handler)
    startstop_callback_handler = CallbackQueryHandler(
        start_stop, pattern=r"close_menu")
    dispatcher.add_handler(startstop_callback_handler)

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_")

    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats)
    is_chat_allowed_handler = MessageHandler(Filters.group, is_chat_allowed)
    about_callback_handler = CallbackQueryHandler(Nisshoku_about_callback, pattern=r"nisshokuabout_")

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(start_p_handler)

    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(about_callback_handler)
    # dispatcher.add_handler(help_staff_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(is_chat_allowed_handler)
    dispatcher.add_error_handler(error_handler)
    
    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(
                url=URL + TOKEN,
                certificate=open(
                    CERT_PATH,
                    "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)
            client.run_until_disconnected()

    else:
        LOGGER.info("Ara Ara uhuhuhuhuhuhuhuhuhu....")
        updater.start_polling(timeout=15, read_latency=4)
        updater.bot.send_message(
            chat_id=MESSAGE_DUMP,
            text="Ara Ara, Akeno is running @PresidentRias @SekieRyu")
        client.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    client.start(bot_token=TOKEN)
    nyaa.start()
    main()
