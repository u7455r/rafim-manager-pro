import os
import sys
import time
import re
import sqlite3
import telebot
from telebot import types
from keep_alive import keep_alive

print("--- Initializing Rafim Manager Engine Pro Max ---", flush=True)

BOT_TOKEN = "8963227766:AAHcXLL-eceHed6xeGYoNAXHntOf05dxAnE"
bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

ADMIN_USER_ID = 8243644026
ADMIN_USERNAME = "rafimhossen"

REQ_GROUP_LINK = "https://t.me/+M2fdG9hbU3tlOGQ1"
REQ_CHANNEL = "@rafimhossen3"
REQ_CHANNEL_LINK = "https://t.me/rafimhossen3"
DB_FILE = "smart_rose_pro.db"

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS warns (chat_id INTEGER, user_id INTEGER, count INTEGER, PRIMARY KEY (chat_id, user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS filters (chat_id INTEGER, keyword TEXT, reply TEXT, PRIMARY KEY (chat_id, keyword))''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY)''')
    c.execute('''CREATE TABLE IF NOT EXISTS seen_users (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

def get_warn_count(chat_id, user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT count FROM warns WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0

def add_warn(chat_id, user_id):
    try:
        curr = get_warn_count(chat_id, user_id) + 1
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO warns VALUES (?, ?, ?)", (chat_id, user_id, curr))
        conn.commit()
        conn.close()
        return curr
    except Exception:
        return 1

def reset_user_warns(chat_id, user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM warns WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        conn.commit()
        conn.close()
    except Exception:
        pass

def save_filter(chat_id, keyword, reply):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO filters VALUES (?, ?, ?)", (chat_id, keyword.lower(), reply))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def delete_filter(chat_id, keyword):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM filters WHERE chat_id=? AND keyword=?", (chat_id, keyword.lower()))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_filters(chat_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT keyword, reply FROM filters WHERE chat_id=?", (chat_id,))
        rows = c.fetchall()
        conn.close()
        return dict(rows)
    except Exception:
        return {}

def register_chat(chat_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO chats VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_all_chats():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT chat_id FROM chats")
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception:
        return []

def get_total_users():
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM seen_users")
        cnt = c.fetchone()[0]
        conn.close()
        return cnt
    except Exception:
        return 0

def is_new_user(user_id):
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT user_id FROM seen_users WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO seen_users VALUES (?)", (user_id,))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False
    except Exception:
        return False

# ==================== HELPERS ====================
def is_owner(message):
    if not message.from_user:
        return False
    return message.from_user.id == ADMIN_USER_ID or message.from_user.username == ADMIN_USERNAME

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(REQ_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

def notify_admin(text):
    try:
        bot.send_message(ADMIN_USER_ID, text)
    except Exception as e:
        print(f"Notify failed: {e}", flush=True)

def is_group_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

def get_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🔄 রিস্টার্ট করুন"))
    markup.add(types.KeyboardButton("📖 কমান্ড লিস্ট"), types.KeyboardButton("👤 আমার আইডি ও তথ্য"))
    markup.add(types.KeyboardButton("📊 বটের স্ট্যাটাস"), types.KeyboardButton("🛡️ অ্যাডমিনগণ"))
    markup.add(types.KeyboardButton("📜 গ্রুপের নিয়ম"), types.KeyboardButton("➕ গ্রুপে যুক্ত করুন"))
    markup.add(types.KeyboardButton("📢 চ্যানেলে যুক্ত করুন"))
    return markup

def get_join_markup():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 ১. চ্যানেলে জয়েন করুন (@rafimhossen3)", url=REQ_CHANNEL_LINK),
        types.InlineKeyboardButton("👥 ২. গ্রুপে জয়েন করুন (আবশ্যক)", url=REQ_GROUP_LINK),
        types.InlineKeyboardButton("✅ জয়েন সম্পন্ন করেছি (Verify)", callback_data="verify_channel_sub")
    )
    return markup

# ==================== CHANNEL POST AUTO REPLY & LIKE/REACTION ====================
def generate_smart_reply(text):
    t = text.lower() if text else ""
    if any(w in t for w in ["giveaway", "গিভঅ্যাওয়ে", "premium", "প্রিমিয়াম", "winner"]):
        return "🎉 দুর্দান্ত গিভঅ্যাওয়ে! সবাই নিয়ম মেনে অংশ নিন এবং ইউজারনেম কমেন্ট করুন! 🚀✨"
    elif any(w in t for w in ["update", "আপডেট", "নতুন", "রিলিজ"]):
        return "🔥 দারুণ আপডেট! নতুন ফিচারের সাহায্যে ম্যানেজমেন্ট আরও সহজ হবে। 👏"
    elif any(w in t for w in ["কুইজ", "quiz", "প্রশ্ন"]):
        return "💡 চমৎকার একটি প্রশ্ন! সঠিক উত্তরটি কমেন্টে দ্রুত জানিয়ে দিন। 🎯"
    else:
        return "💎 গুরুত্বপূর্ণ পোস্ট! সবাই লাইক/রিঅ্যাক্ট দিয়ে পাশে থাকুন। 👍"

@bot.channel_post_handler(content_types=['text', 'photo', 'video', 'document'])
def handle_channel_post(message):
    post_text = message.text or message.caption or ""
    reply_text = generate_smart_reply(post_text)

    try:
        bot.set_message_reaction(
            message.chat.id,
            message.message_id,
            [types.ReactionTypeEmoji("❤️")],
            is_big=False
        )
    except Exception as e:
        print(f"Reaction error: {e}")

    try:
        bot.reply_to(message, reply_text)
    except Exception as e:
        print(f"Post reply error: {e}", flush=True)

# ==================== GROUP WELCOME & AUTO RESPONDER ====================
@bot.message_handler(content_types=['new_chat_members'])
def track_new_members_and_groups(message):
    register_chat(message.chat.id)
    my_id = bot.get_me().id

    for member in message.new_chat_members:
        if member.id == my_id:
            adder = message.from_user
            adder_info = f"{adder.first_name} (@{adder.username})" if adder else "অ্যাডমিন"
            alert = (
                "🤖 **বটকে নতুন একটি গ্রুপে যুক্ত করা হয়েছে!**\n\n"
                f"🏷️ গ্রুপের নাম: {message.chat.title}\n"
                f"🆔 গ্রুপ আইডি: `{message.chat.id}`\n"
                f"👤 অ্যাড করেছে: {adder_info}"
            )
            notify_admin(alert)
            return

        user_tag = f"@{member.username}" if member.username else f"[{member.first_name}](tg://user?id={member.id})"
        group_title = message.chat.title or "আমাদের গ্রুপ"

        welcome_text = f"Hi {user_tag} welcome to {group_title}!"
        channel_box_markup = types.InlineKeyboardMarkup(row_width=1)
        channel_box_markup.add(types.InlineKeyboardButton("Telegram Channel ↗", url=REQ_CHANNEL_LINK))

        try:
            bot.send_message(message.chat.id, welcome_text, reply_markup=channel_box_markup, parse_mode='Markdown')
        except Exception as e:
            print(f"Welcome error: {e}")

@bot.message_handler(content_types=['left_chat_member'])
def handle_left_member(message):
    register_chat(message.chat.id)
    user = message.left_chat_member
    if user.id == bot.get_me().id:
        return

    user_tag = f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"
    farewell_text = f"👋 বিদায়, {user_tag}!\n🚶 আপনি আমাদের গ্রুপ ছেড়ে চলে গেলেন। শুভকামনা রইল! ✨"
    farewell_markup = types.InlineKeyboardMarkup(row_width=1)
    farewell_markup.add(types.InlineKeyboardButton("📢 অফিসিয়াল চ্যানেলে যুক্ত থাকুন ↗", url=REQ_CHANNEL_LINK))

    try:
        bot.send_message(message.chat.id, farewell_text, reply_markup=farewell_markup, parse_mode='Markdown')
    except Exception as e:
        print(f"Goodbye error: {e}")

def generate_group_smart_answer(text):
    t = text.lower() if text else ""
    if any(w in t for w in ["কেমন আছিস", "কেমন আছেন", "how are you"]):
        return "আলহামদুলিল্লাহ, আমি দারুণ আছি! আপনি কেমন আছেন? 😊"
    elif any(w in t for w in ["বট", "bot", "admin", "মালিক"]):
        return "আমি আপনাদের সহযোগিতায় সার্বক্ষণিক প্রস্তুত। ওনার: @rafimhossen 🛡️"
    elif any(w in t for w in ["সাহায্য", "help", "কমান্ড"]):
        return "যেকোনো তথ্যের জন্য বটের ইনবক্সে গিয়ে /start দিতে পারেন। 📌"
    else:
        return "আপনার বার্তাটি লক্ষ্য করেছি! গ্রুপে আলোচনা চালিয়ে যান। 👍"

@bot.message_handler(func=lambda msg: msg.chat.type in ['group', 'supergroup'])
def group_chat_auto_responder(message):
    if not message.text:
        return
    register_chat(message.chat.id)

    is_anon = message.sender_chat and message.sender_chat.id == message.chat.id
    user_is_adm = is_anon or (message.from_user and is_group_admin(message.chat.id, message.from_user.id)) or is_owner(message)

    if re.search(r'(https?://[^\s]+|t\.me/[^\s]+|telegram\.me/[^\s]+)', message.text):
        if not user_is_adm:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(message.chat.id, f"⚠️ [{message.from_user.first_name}](tg://user?id={message.from_user.id}), লিঙ্ক দেওয়া সম্পূর্ণ নিষিদ্ধ!", parse_mode='Markdown')
            except Exception:
                pass
            return

    filters = get_filters(message.chat.id)
    text_lower = message.text.lower()
    for kw, resp in filters.items():
        if kw in text_lower:
            bot.reply_to(message, resp)
            return

    if "@" in message.text or "?" in message.text or message.reply_to_message:
        reply_ans = generate_group_smart_answer(message.text)
        try:
            bot.reply_to(message, reply_ans)
        except Exception:
            pass

# ==================== START & FORCE SUB ====================
@bot.callback_query_handler(func=lambda call: call.data == "verify_channel_sub")
def check_channel_verification(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ ভেরিফিকেশন সফল হয়েছে!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_welcome(call.message, call.from_user)
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি!", show_alert=True)

def send_welcome(message, user=None):
    u = user if user else message.from_user
    text = f"🌹 **স্বাগতম, {u.first_name}!** 👋\n\nআমি আপনার স্মার্ট গ্রুপ ম্যানেজার ও অটোমেশন রোবট।"
    bot.send_message(message.chat.id, text, reply_markup=get_reply_keyboard(), parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def handle_start(message):
    register_chat(message.chat.id)
    u = message.from_user

    if message.chat.type == 'private':
        if is_new_user(u.id):
            info = (
                "👤 **নতুন ইউজার বট চালু করেছে!**\n\n"
                f"• নাম: {u.first_name} {u.last_name or ''}\n"
                f"• ইউজারনেম: @{u.username or 'নাই'}\n"
                f"• আইডি: `{u.id}`"
            )
            notify_admin(info)

        if not is_subscribed(u.id):
            bot.send_message(
                message.chat.id,
                "⚠️ **বটটি ব্যবহার করতে হলে অবশ্যই আমাদের চ্যানেল ও গ্রুপে জয়েন থাকতে হবে!**\n\nনিচের বাটনে চাপ দিয়ে ভেরিফাই করুন:",
                reply_markup=get_join_markup(),
                parse_mode='Markdown'
            )
            return
        send_welcome(message)
    else:
        bot.reply_to(message, "✅ বট সক্রিয় রয়েছে!")

# ==================== EXTRA POWERFUL COMMANDS ====================
@bot.message_handler(commands=['status'])
def group_status_check(message):
    register_chat(message.chat.id)
    chats_cnt = len(get_all_chats())
    users_cnt = get_total_users()
    grp_filters = len(get_filters(message.chat.id)) if message.chat.type != 'private' else 0

    status_card = (
        "📊 **বট পারফরম্যান্স কার্ড:**\n\n"
        f"🤖 **স্ট্যাটাস:** অনলাইন 🟢\n"
        f"👥 **মোট ইউজার:** {users_cnt} জন\n"
        f"🌐 **সংযুক্ত গ্রুপ:** {chats_cnt} টি\n"
        f"🎯 **গ্রুপে সক্রিয় ফিল্টার:** {grp_filters} টি\n"
        f"⚡ **সার্ভার রেসপন্স:** অতি দ্রুত"
    )
    bot.reply_to(message, status_card, parse_mode='Markdown')

@bot.message_handler(commands=['info'])
def user_info_card(message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    warns = get_warn_count(message.chat.id, target.id) if message.chat.type != 'private' else 0
    info_text = (
        "👤 **মেম্বার প্রোফাইল তথ্য:**\n\n"
        f"• **নাম:** {target.first_name} {target.last_name or ''}\n"
        f"• **ইউজারনেম:** @{target.username or 'নাই'}\n"
        f"• **আইডি:** `{target.id}`\n"
        f"• **ওয়ার্নিং সংখ্যা:** {warns}/3\n"
        f"• **বট ইউজার:** {'হ্যাঁ' if target.is_bot else 'না'}"
    )
    bot.reply_to(message, info_text, parse_mode='Markdown')

@bot.message_handler(commands=['lockdown'])
def emergency_lockdown(message):
    if message.chat.type == 'private':
        return
    is_anon = message.sender_chat and message.sender_chat.id == message.chat.id
    if not (is_anon or is_group_admin(message.chat.id, message.from_user.id) or is_owner(message)):
        bot.reply_to(message, "❌ এই কমান্ডের অনুমতি আপনার নেই!")
        return

    try:
        bot.set_chat_permissions(message.chat.id, types.ChatPermissions(can_send_messages=False))
        bot.send_message(message.chat.id, "🔒 **গ্রুপে লকডাউন জারি করা হয়েছে!**\nসাধারণ সদস্যরা এখন কথা বলতে পারবেন না।", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"ত্রুটি: {e}")

@bot.message_handler(commands=['unlockdown'])
def release_lockdown(message):
    if message.chat.type == 'private':
        return
    is_anon = message.sender_chat and message.sender_chat.id == message.chat.id
    if not (is_anon or is_group_admin(message.chat.id, message.from_user.id) or is_owner(message)):
        bot.reply_to(message, "❌ এই কমান্ডের অনুমতি আপনার নেই!")
        return

    try:
        bot.set_chat_permissions(
            message.chat.id,
            types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        bot.send_message(message.chat.id, "🔓 **লকডাউন তুলে নেওয়া হয়েছে!**\nএখন সবাই চ্যাট করতে পারবেন।", parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"ত্রুটি: {e}")

# ==================== REPLY KEYBOARD HANDLER ====================
@bot.message_handler(func=lambda msg: msg.text in [
    "🔄 রিস্টার্ট করুন", "📖 কমান্ড লিস্ট", "👤 আমার আইডি ও তথ্য", "📊 বটের স্ট্যাটাস", "🛡️ অ্যাডমিনগণ", "📜 গ্রুপের নিয়ম", "➕ গ্রুপে যুক্ত করুন", "📢 চ্যানেলে যুক্ত করুন"
])
def reply_buttons_handler(message):
    register_chat(message.chat.id)
    if message.chat.type == 'private' and not is_subscribed(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ অনুগ্রহ করে আগে চ্যানেল ও গ্রুপে জয়েন করুন!", reply_markup=get_join_markup())
        return

    bot_info = bot.get_me()
    if message.text == "🔄 রিস্টার্ট করুন":
        send_welcome(message)
    elif message.text == "📊 বটের স্ট্যাটাস":
        group_status_check(message)
    elif message.text == "📖 কমান্ড লিস্ট":
        help_cmd_list = (
            "🛠️ **প্রয়োজনীয় কমান্ডসমূহ:**\n\n"
            "• `/warn` - সতর্ক করতে (রিপ্লাই দিন)\n"
            "• `/pin` - মেসেজ পিন করতে\n"
            "• `/purge` - দ্রুত মেসেজ মুছতে\n"
            "• `/info` - মেম্বারের তথ্য জানতে\n"
            "• `/status` - সিস্টেম স্ট্যাটাস\n"
            "• `/lockdown` - চ্যাট সাময়িক বন্ধ করতে\n"
            "• `/unlockdown` - চ্যাট উন্মুক্ত করতে\n"
            "• `/addfilter শব্দ | উত্তর` - অটো রিপ্লাই (ওনারের জন্য)"
        )
        bot.reply_to(message, help_cmd_list, parse_mode='Markdown')
    elif message.text == "👤 আমার আইডি ও তথ্য":
        u = message.from_user
        bot.reply_to(message, f"👤 **তথ্য:**\n• নাম: {u.first_name}\n• ইউজারনেম: @{u.username or 'নাই'}\n• আইডি: `{u.id}`", parse_mode='Markdown')
    elif message.text == "🛡️ অ্যাডমিনগণ":
        bot.reply_to(message, "গ্রুপে গিয়ে `/admins` দিলে তালিকা দেখা যাবে।")
    elif message.text == "📜 গ্রুপের নিয়ম":
        bot.reply_to(message, "📜 গ্রুপে কোনো লিঙ্ক, স্প্যাম বা খারাপ আচরণ নিষিদ্ধ।")
    elif message.text == "➕ গ্রুপে যুক্ত করুন":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Add Bot to Group", url=f"https://t.me/{bot_info.username}?startgroup=true"))
        bot.send_message(message.chat.id, "গ্রুপে যুক্ত করতে চাপ দিন:", reply_markup=m)
    elif message.text == "📢 চ্যানেলে যুক্ত করুন":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📢 Add Bot to Channel", url=f"https://t.me/{bot_info.username}?startchannel=true"))
        bot.send_message(message.chat.id, "চ্যানেলে যুক্ত করতে চাপ দিন:", reply_markup=m)

# ==================== STRICT OWNER-ONLY FILTERS ====================
@bot.message_handler(commands=['addfilter', 'filter'])
def handle_add_filter(message):
    register_chat(message.chat.id)

    if not is_owner(message):
        bot.reply_to(message, "❌ আপনি এই বটের ওনার নন! শুধুমাত্র @rafimhossen ফিল্টার যুক্ত করতে পারবেন।")
        return

    full_text = message.text.split(maxsplit=1)
    if len(full_text) < 2 or '|' not in full_text[1]:
        bot.reply_to(message, "⚠️ সঠিক নিয়ম: `/addfilter শব্দ | উত্তর`", parse_mode='Markdown')
        return

    parts = full_text[1].split('|', 1)
    kw = parts[0].strip().lower()
    ans = parts[1].strip()

    save_filter(message.chat.id, kw, ans)
    bot.reply_to(message, f"🎯 ফিল্টার সেভ হয়েছে: `{kw}`", parse_mode='Markdown')

@bot.message_handler(commands=['stop'])
def handle_stop_filter(message):
    register_chat(message.chat.id)
    if not is_owner(message):
        bot.reply_to(message, "❌ শুধুমাত্র ওনার ফিল্টার মুছে দিতে পারেন।")
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ ব্যবহার: `/stop শব্দ`", parse_mode='Markdown')
        return

    kw = parts[1].strip().lower()
    delete_filter(message.chat.id, kw)
    bot.reply_to(message, f"🗑️ ফিল্টার মুছে দেওয়া হয়েছে: `{kw}`", parse_mode='Markdown')

@bot.message_handler(commands=['filters'])
def handle_list_filters(message):
    register_chat(message.chat.id)
    filters = get_filters(message.chat.id)
    if not filters:
        bot.reply_to(message, "📂 এই গ্রুপে কোনো ফিল্টার নেই।", parse_mode='Markdown')
        return
    txt = "📋 **সক্রিয় ফিল্টার তালিকা:**\n\n"
    for k in filters.keys():
        txt += f"• `{k}`\n"
    bot.reply_to(message, txt, parse_mode='Markdown')

# ==================== ADMIN ACTIONS ====================
@bot.message_handler(commands=['pin', 'unpin', 'warn', 'ban', 'kick', 'mute', 'purge'])
def handle_admin_tools(message):
    if message.chat.type == 'private':
        return
    register_chat(message.chat.id)

    is_anon = message.sender_chat and message.sender_chat.id == message.chat.id
    user_is_adm = is_anon or (message.from_user and is_group_admin(message.chat.id, message.from_user.id)) or is_owner(message)

    if not user_is_adm:
        bot.reply_to(message, "❌ এই কমান্ডটি শুধু গ্রুপের অ্যাডমিনদের জন্য!")
        return

    cmd = message.text.split()[0].split('@')[0].replace('/', '').lower()
    orig = message.reply_to_message

    if not orig and cmd != 'purge':
        bot.reply_to(message, "⚠️ মেম্বারের মেসেজে রিপ্লাই দিয়ে কমান্ড দিন।")
        return

    try:
        if cmd == 'pin':
            bot.pin_chat_message(message.chat.id, orig.message_id)
            bot.reply_to(message, "📌 মেসেজটি পিন করা হয়েছে!")
        elif cmd == 'unpin':
            bot.unpin_chat_message(message.chat.id, orig.message_id)
            bot.reply_to(message, "📌 মেসেজটি আনপিন করা হয়েছে!")
        elif cmd == 'warn':
            target = orig.from_user
            if not target:
                return
            count = add_warn(message.chat.id, target.id)
            if count >= 3:
                bot.restrict_chat_member(message.chat.id, target.id, permissions=types.ChatPermissions(can_send_messages=False))
                bot.reply_to(message, f"🚫 [{target.first_name}](tg://user?id={target.id}) ৩ বার সতর্ক পেয়ে মিউট হয়েছেন!", parse_mode='Markdown')
                reset_user_warns(message.chat.id, target.id)
            else:
                bot.reply_to(message, f"⚠️ [{target.first_name}](tg://user?id={target.id}) সতর্কবার্তা: **{count}/3**", parse_mode='Markdown')
        elif cmd == 'ban':
            if orig.from_user:
                bot.ban_chat_member(message.chat.id, orig.from_user.id)
                bot.reply_to(message, "🚫 মেম্বারকে ব্যান করা হয়েছে।")
        elif cmd == 'kick':
            if orig.from_user:
                bot.ban_chat_member(message.chat.id, orig.from_user.id)
                bot.unban_chat_member(message.chat.id, orig.from_user.id)
                bot.reply_to(message, "👢 মেম্বারকে বহিষ্কার করা হয়েছে।")
        elif cmd == 'mute':
            if orig.from_user:
                bot.restrict_chat_member(message.chat.id, orig.from_user.id, permissions=types.ChatPermissions(can_send_messages=False))
                bot.reply_to(message, "🔇 মেম্বারকে মিউট করা হয়েছে।")
        elif cmd == 'purge':
            if not orig:
                bot.reply_to(message, "⚠️ যেখান থেকে ডিলিট শুরু করবেন সেখানে রিপ্লাই দিন।")
                return
            start_id = orig.message_id
            end_id = message.message_id
            for mid in range(start_id, end_id + 1):
                try:
                    bot.delete_message(message.chat.id, mid)
                except Exception:
                    pass
    except Exception as e:
        bot.reply_to(message, f"ত্রুটি: {e}")

# ==================== RUNNER ====================
if __name__ == '__main__':
    keep_alive()
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception:
        pass

    bot_info = bot.get_me()
    print(f"Bot Online: @{bot_info.username}. Ready!", flush=True)

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Connection recovery: {e}", flush=True)
            time.sleep(3)
