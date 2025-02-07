import datetime
import html
import os
import platform
import subprocess
import time
from platform import python_version

import requests
import speedtest
from psutil import boot_time, cpu_percent, disk_usage, virtual_memory
from spamwatch import __version__ as __sw__
from telegram import ParseMode, __version__
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, run_async

from Elizabeth import MESSAGE_DUMP, OWNER_ID, dispatcher
from Elizabeth.modules.helper_funcs.alternate import typing_action
from Elizabeth.modules.helper_funcs.filters import CustomFilters

since_time_start = time.time()

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

@run_async
@typing_action
def leavechat(update, context):
    args = context.args
    msg = update.effective_message
    if args:
        chat_id = int(args[0])

    else:
        msg.reply_text("Bro.. Give Me ChatId And boom!!")
    try:
        titlechat = context.bot.get_chat(chat_id).title
        context.bot.sendMessage(
            chat_id,
            "I'm here trying to survive, but this world is too cruel, goodbye everyone 😌",
        )
        context.bot.leaveChat(chat_id)
        msg.reply_text("I have left the group {}".format(titlechat))

    except BadRequest as excp:
        if excp.message == "bot is not a member of the supergroup chat":
            msg = update.effective_message.reply_text(
                "I'Am not Joined The Group, Maybe You set wrong id or I Already Kicked out"
            )

        else:
            return



@typing_action
def ping(update, context):
    msg = update.effective_message
    start_time = time.time()
    message = msg.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    uptime = get_readable_time((time.time() - since_time_start))
    message.edit_text(
        "Ara Ara!!\n"
        "<b>Ping :</b> <code>{}</code>\n"
        "<b>Uptime :</b> <code>{}</code>".format(ping_time, uptime),
        parse_mode=ParseMode.HTML        
    )

   
    
@run_async
@typing_action
def speedtst(update, context):        
    speed = speedtest.Speedtest()
    speed.get_best_server()
    speed.download()
    speed.upload()
    replymsg = "Ookla speedtest results:"
    speedtest_image = speed.results.share()
    update.effective_message.reply_photo(photo=speedtest_image, caption=replymsg)
    


@run_async
@typing_action
def system_status(update, context):
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    status = "<b>======[ SYSTEM INFO ]======</b>\n\n"
    status += "<b>System uptime:</b> <code>" + str(uptime) + "</code>\n"

    uname = platform.uname()
    status += "<b>System:</b> <code>" + str(uname.system) + "</code>\n"
    status += "<b>Node name:</b> <code>" + str(uname.node) + "</code>\n"
    status += "<b>Release:</b> <code>" + str(uname.release) + "</code>\n"
    status += "<b>Version:</b> <code>" + str(uname.version) + "</code>\n"
    status += "<b>Machine:</b> <code>" + str(uname.machine) + "</code>\n"
    status += "<b>Processor:</b> <code>" + str(uname.processor) + "</code>\n\n"

    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    status += "<b>CPU usage:</b> <code>" + str(cpu) + " %</code>\n"
    status += "<b>Ram usage:</b> <code>" + str(mem[2]) + " %</code>\n"
    status += "<b>Storage used:</b> <code>" + str(disk[3]) + " %</code>\n\n"
    status += "<b>Python version:</b> <code>" + python_version() + "</code>\n"
    status += "<b>Library version:</b> <code>" + str(__version__) + "</code>\n"
    status += "<b>Spamwatch API:</b> <code>" + str(__sw__) + "</code>\n"
    context.bot.sendMessage(
        update.effective_chat.id, status, parse_mode=ParseMode.HTML
    )


def speed_convert(size):
    """Hi human, you can't read bytes?"""
    power = 2 ** 10
    zero = 0
    units = {0: "", 1: "Kb/s", 2: "Mb/s", 3: "Gb/s", 4: "Tb/s"}
    while size > power:
        size /= power
        zero += 1
    return f"{round(size, 2)} {units[zero]}"


@run_async
@typing_action
def gitpull(update, context):
    sent_msg = update.effective_message.reply_text(
        "Pulling all changes from remote..."
    )
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = (
        sent_msg.text
        + "\n\nChanges pulled... I guess..\nContinue to restart with /reboot "
    )
    sent_msg.edit_text(sent_msg_text)


@run_async
@typing_action
def restart(update, context):
    user = update.effective_message.from_user

    update.effective_message.reply_text(
        "Starting a new instance and shutting down this one"
    )

    if MESSAGE_DUMP:
        datetime_fmt = "%H:%M - %d-%m-%Y"
        current_time = datetime.datetime.utcnow().strftime(datetime_fmt)
        message = (
            f"<b>Bot Restarted </b>"
            f"<b>By :</b> <code>{html.escape(user.first_name)}</code>"
            f"<b>\nDate Bot Restart : </b><code>{current_time}</code>"
        )
        context.bot.send_message(
            chat_id=MESSAGE_DUMP,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    os.system("bash start")


@run_async
@typing_action
def get_bot_ip(update, context):
    """Sends the bot's IP address, so as to be able to ssh in if necessary.
    OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


IP_HANDLER = CommandHandler(
    "ip", get_bot_ip, filters=Filters.chat(OWNER_ID)
)
PING_HANDLER = CommandHandler(
    "ping", ping
)
SPEED_HANDLER = CommandHandler(
    "speedtest", speedtst
)
SYS_STATUS_HANDLER = CommandHandler(
    "sysinfo", system_status, filters=CustomFilters.dev_filter
)
LEAVECHAT_HANDLER = CommandHandler(
    ["leavechat", "leavegroup", "leave"],
    leavechat,
    pass_args=True,
    filters=CustomFilters.dev_filter
)
GITPULL_HANDLER = CommandHandler(
    "gitpull", gitpull, filters=CustomFilters.dev_filter
)
RESTART_HANDLER = CommandHandler(
    "reboot", restart, filters=CustomFilters.dev_filter
)

dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(SPEED_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(SYS_STATUS_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(GITPULL_HANDLER)
dispatcher.add_handler(RESTART_HANDLER)
