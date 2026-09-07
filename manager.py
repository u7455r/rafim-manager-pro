import os
import sys
import time
import re
import sqlite3
import telebot
from telebot import types
from keep_alive import keep_alive

print("--- Initializing Rafim Rose Premium Ultimate Engine ---", flush=True)

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

# ==================== MODULE DETAILS ====================
MODULE_DETAILS = {
    "admin": "🛡️ **Admin Module (অ্যাডমিন নিয়ন্ত্রণ):**\n\nগ্রুপের সকল অ্যাডমিনিস্ট্রেটিভ কাজ পরিচালনা করার জন্য।\n\n📌 **কমান্ডসমূহ:**\n• `/admins` - গ্রুপের বর্তমান অ্যাডমিন তালিকা দেখতে।\n• `/promote` - কোনো মেম্বারকে অ্যাডমিন বানাতে (রিপ্লাই দিন)।\n• `/demote` - অ্যাডমিন পদ বাতিল করতে।",
    "antiflood": "🌊 **Antiflood Module (ফ্লাড প্রটেকশন):**\n\nগ্রুপে দ্রুত মেসেজ পাঠিয়ে ফ্লাড করা ঠেকানোর সিস্টেম।\n\n📌 **কমান্ডসমূহ:**\n• `/flood` - ফ্লাড সেটিংস চেক করতে।\n• `/setflood <সংখ্যা>` - সর্বোচ্চ কতটি মেসেজের পর মিউট হবে সেট করুন।",
    "antiraid": "⚔️ **AntiRaid Module (রেইড প্রতিরোধ):**\n\nগ্রুপে হঠাৎ বট অ্যাটাক বা রেইড আক্রমণ হলে গ্রুপ রক্ষা করুন।\n\n📌 **কমান্ডসমূহ:**\n• `/antiraid on/off` - অটোমেটিক লকডাউন সক্রিয় বা নিষ্ক্রিয় করুন।",
    "approval": "🤝 **Approval Module (অনুমোদন):**\n\nনির্দিষ্ট মেম্বারকে স্প্যাম ফিল্টার বা ব্লকলিস্ট ছাড়া চ্যাট করার অনুমতি দিন।\n\n📌 **কমান্ডসমূহ:**\n• `/approve` - মেম্বারকে অনুমোদন দিন।\n• `/unapprove` - অনুমোদন প্রত্যাহার করুন।",
    "bans": "🚫 **Bans Module (ব্যান ও বহিষ্কার):**\n\nঅবাঞ্ছিত মেম্বারদের সহজে গ্রুপ থেকে বের বা স্থায়ী ব্যান করার সিস্টেম।\n\n📌 **কমান্ডসমূহ:**\n• `/ban` - মেম্বারকে আজীবনের জন্য ব্যান করতে।\n• `/kick` - মেম্বারকে গ্রুপ থেকে বের করে দিতে।\n• `/unban` - ব্যান তুলে নিতে।",
    "blocklists": "⛔ **Blocklists (ব্লকলিস্ট ফিল্টার):**\n\nখারাপ শব্দ, লিংক বা অযাচিত মেসেজ গ্রুপে স্বয়ংক্রিয়ভাবে ব্লক রাখার সিস্টেম।",
    "captcha": "🤖 **CAPTCHA (ক্যাপচা ভেরিফিকেশন):**\n\nগ্রুপে যাতে কোনো ফেক বট ঢুকতে না পারে সেজন্য অটো ক্যাপচা টেস্ট।",
    "cleancom": "🧹 **Clean Commands (কমান্ড ক্লিনার):**\n\nঅ্যাডমিনদের দেওয়া কমান্ড মেসেজ কাজ শেষ হওয়ার সাথে সাথে মুছে ফেলার সিস্টেম।",
    "cleanserv": "🧽 **Clean Service (সার্ভিস মেসেজ রিমুভার):**\n\nমেম্বার জয়েন ও লিভ করার বিরক্তি মেসেজগুলো স্বয়ংক্রিয়ভাবে ডিলিট করার মোড।",
    "connect": "🔗 **Connect (ইনবক্স কানেকশন):**\n\nবটের ইনবক্স থেকে গ্রুপ সরাসরি পরিচালনা করার কানেকশন মোড।",
    "disabling": "📴 **Disabling (কমান্ড নিয়ন্ত্রণ):**\n\nগ্রুপের মেম্বারদের জন্য নির্দিষ্ট কোনো কমান্ড সাময়িকভাবে বন্ধ রাখার ব্যবস্থা।",
    "federation": "🌐 **Federation (ফেডারেশন নেটওয়ার্ক):**\n\nআপনার একাধিক গ্রুপ একসাথে যুক্ত করে এক ক্লিকে সব গ্রুপ থেকে ব্যান করার নেটওয়ার্ক।",
    "filters": "🎯 **Filters (অটো রিপ্লাই - ওনার নিয়ন্ত্রণ):**\n\nনির্দিষ্ট শব্দ লিখলে বট থেকে স্বয়ংক্রিয় উত্তর পাওয়ার ব্যবস্থা।\n\n📌 **প্রয়োজনীয় কমান্ডসমূহ:**\n• `/addfilter শব্দ | উত্তর` - নতুন ফিল্টার যুক্ত করুন।\n• `/filters` - সক্রিয় ফিল্টারের তালিকা।\n• `/stop শব্দ` - ফিল্টার মুছে দিন।",
    "formatting": "✍️ **Formatting (টেক্সট স্টাইল):**\n\nবোল্ড, ইটালিক, কোড ব্লক এবং টেলিগ্রাম প্রিমিয়াম ফরম্যাটিং সহায়িকা।",
    "greetings": "👋 **Greetings (স্বাগতম ও বিদায় বার্তা):**\n\nনতুন মেম্বারদের স্বাগতম বার্তা এবং গ্রুপ ছেড়ে যাওয়া মেম্বারদের বিদায় নোটিস।",
    "backup": "📦 **Backup (ব্যাকআপ মোড):**\n\nগ্রুপের সকল ফিল্টার, রুলস ও কনফিগারেশন ডাটা নিরাপদে ব্যাকআপ নেওয়া।",
    "language": "🌍 **Language (ভাষা নির্বাচন):**\n\nবটের ভাষা পরিবর্তন করার সেটিংস প্যানেল।",
    "locks": "🔒 **Locks (মিডিয়া ও লিংক লক):**\n\nগ্রুপে স্টিকার, জিআইএফ, ছবি বা লিংক আলাদা আলাদাভাবে বন্ধ করার লক সিস্টেম।",
    "logs": "📝 **Logs (লাইভ হিস্ট্রি):**\n\nগ্রুপের সমস্ত নোটিফিকেশন ও অ্যাকশন লাইভ প্রাইভেট চ্যানেলে দেখার ব্যবস্থা।",
    "misc": "⚙️ **Misc (বিবিধ ফিচার):**\n\nইউজার ইনফো, আইডি খোঁজা এবং অন্যান্য প্রয়োজনীয় কুইক টুলস।",
    "notes": "📌 **Notes (সংরক্ষিত তথ্য):**\n\nগ্রুপে দরকারি লেখা বা লিঙ্ক সেভ করে রাখার নোটস মডিউল।",
    "pin": "📍 **Pin Module (পিন কন্ট্রোল):**\n\nমেসেজে রিপ্লাই দিয়ে সহজেই চ্যাটে পিন বা আনপিন করুন।\n\n📌 **কমান্ডসমূহ:**\n• `/pin` - মেসেজ পিন করতে।\n• `/unpin` - মেসেজ আনপিন করতে।",
    "privacy": "🔐 **Privacy (নিরাপত্তা গ্যারান্টি):**\n\nগ্রুপের সকল ডাটা ১০০% সুরক্ষিত ও এনক্রিপ্টেড রাখার পলিসি।",
    "purges": "🗑️ **Purges (এক ক্লিকে মেসেজ ডিলিট):**\n\nমেসেজে রিপ্লাই দিয়ে দ্রুত এক সাথে শত শত মেসেজ ডিলিট করুন।\n\n📌 **কমান্ড:**\n• `/purge` - রিপ্লাই করা মেসেজ থেকে নিচে সব ডিলিট হবে।",
    "reports": "📢 **Reports (রিপোর্ট সিস্টেম):**\n\nসাধারণ মেম্বাররা কোনো স্প্যাম মেসেজে `@admin` লিখে অ্যাডমিনদের দ্রুত অ্যালার্ট করতে পারবে।",
    "rules": "📜 **Rules (গ্রুপের নিয়মাবলী):**\n\nগ্রুপের যাবতীয় রুলস মেম্বারদের সুন্দর বাটন আকারে দেখানোর ব্যবস্থা।",
    "topics": "💬 **Topics (ফোরাম ম্যানেজমেন্ট):**\n\nটেলিগ্রাম ফোরাম গ্রুপের আলাদা আলাদা টপিক ম্যানেজ করার ফিচার।",
    "warnings": "⚠️ **Warnings (সতর্কবার্তা সিস্টেম):**\n\nখারাপ আচরণের জন্য মেম্বারদের ওয়ার্নিং দেওয়ার ব্যবস্থা।\n\n📌 **কমান্ডসমূহ:**\n• `/warn` - মেম্বারকে সতর্ক করুন (৩ বারে মিউট)।\n• `/warns` - মেম্বারের ওয়ার্নিং চেক করতে।",
    "custom": "⭐ **Custom Instances (প্রো মোড):**\n\nবটের বিশেষ প্রিমিয়াম সেটিংস ও অটোমেশন পাওয়ার।"
}

# ==================== DASHBOARD MARKUPS ====================
def get_full_rose_dashboard():
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    row1 = [
        types.InlineKeyboardButton("🛡️ Admin", callback_data="mod_admin"),
        types.InlineKeyboardButton("🌊 Antiflood", callback_data="mod_antiflood"),
        types.InlineKeyboardButton("⚔️ AntiRaid", callback_data="mod_antiraid")
    ]
    row2 = [
        types.InlineKeyboardButton("🤝 Approval", callback_data="mod_approval"),
        types.InlineKeyboardButton("🚫 Bans", callback_data="mod_bans"),
        types.InlineKeyboardButton("⛔ Blocklists", callback_data="mod_blocklists")
    ]
    row3 = [
        types.InlineKeyboardButton("🤖 CAPTCHA", callback_data="mod_captcha"),
        types.InlineKeyboardButton("🧹 Clean Com", callback_data="mod_cleancom"),
        types.InlineKeyboardButton("🧽 Clean Servi", callback_data="mod_cleanserv")
    ]
    row4 = [
        types.InlineKeyboardButton("🔗 Connect", callback_data="mod_connect"),
        types.InlineKeyboardButton("📴 Disabling", callback_data="mod_disabling"),
        types.InlineKeyboardButton("🌐 Federation", callback_data="mod_federation")
    ]
    row5 = [
        types.InlineKeyboardButton("🎯 Filters", callback_data="mod_filters"),
        types.InlineKeyboardButton("✍️ Formatting", callback_data="mod_formatting"),
        types.InlineKeyboardButton("👋 Greetings", callback_data="mod_greetings")
    ]
    row6 = [
        types.InlineKeyboardButton("📦 Backup", callback_data="mod_backup"),
        types.InlineKeyboardButton("🌍 Language", callback_data="mod_language"),
        types.InlineKeyboardButton("🔒 Locks", callback_data="mod_locks")
    ]
    row7 = [
        types.InlineKeyboardButton("📝 Logs", callback_data="mod_logs"),
        types.InlineKeyboardButton("⚙️ Misc", callback_data="mod_misc"),
        types.InlineKeyboardButton("📌 Notes", callback_data="mod_notes")
    ]
    row8 = [
        types.InlineKeyboardButton("📍 Pin", callback_data="mod_pin"),
        types.InlineKeyboardButton("🔐 Privacy", callback_data="mod_privacy"),
        types.InlineKeyboardButton("🗑️ Purges", callback_data="mod_purges")
    ]
    row9 = [
        types.InlineKeyboardButton("📢 Reports", callback_data="mod_reports"),
        types.InlineKeyboardButton("📜 Rules", callback_data="mod_rules"),
        types.InlineKeyboardButton("💬 Topics", callback_data="mod_topics")
    ]
    
    markup.add(*row1)
    markup.add(*row2)
    markup.add(*row3)
    markup.add(*row4)
    markup.add(*row5)
    markup.add(*row6)
    markup.add(*row7)
    markup.add(*row8)
    markup.add(*row9)
    
    markup.row(
        types.InlineKeyboardButton("⚠️ Warnings", callback_data="mod_warnings"),
        types.InlineKeyboardButton("⭐ Custom Instances", callback_data="mod_custom")
    )
    markup.row(
        types.InlineKeyboardButton("💎 VIP Official Channel ↗", url=REQ_CHANNEL_LINK)
    )
    return markup

def get_module_nav_markup():
    # স্ক্রিনশটের মতো পাশাপাশি দুটি বাটন
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.row(
        types.InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_full_menu"),
        types.InlineKeyboardButton("🧑‍💻 Support Admin ↗", url="https://t.me/rafimhossen")
    )
    return markup

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
        types.InlineKeyboardButton("🌟 ১. ভিআইপি চ্যানেলে জয়েন করুন (@rafimhossen3) ↗", url=REQ_CHANNEL_LINK),
        types.InlineKeyboardButton("👥 ২. অফিসিয়াল গ্রুপে জয়েন করুন (আবশ্যক) ↗", url=REQ_GROUP_LINK),
        types.InlineKeyboardButton("✅ জয়েন সম্পন্ন করেছি (Verify)", callback_data="verify_channel_sub")
    )
    return markup

# ==================== CHANNEL POST AUTO REPLY & LIKE/REACTION ====================
def generate_smart_reply(text):
    t = text.lower() if text else ""
    if any(w in t for w in ["giveaway", "গিভঅ্যাওয়ে", "premium", "প্রিমিয়াম", "winner"]):
        return "🎉🔥 দুর্দান্ত ভিআইপি গিভঅ্যাওয়ে! সবাই নিয়ম মেনে অংশ নিন এবং ইউজারনেম কমেন্ট করুন! 🚀💎"
    elif any(w in t for w in ["update", "আপডেট", "নতুন", "রিলিজ"]):
        return "⚡✨ চমৎকার আপডেট! নতুন ফিচারের সাহায্যে গ্রুপ ম্যানেজমেন্ট হবে ১০০% নিখুঁত। 👏👑"
    elif any(w in t for w in ["কুইজ", "quiz", "প্রশ্ন"]):
        return "💡🎯 ব্রিলিয়ান্ট একটি প্রশ্ন! সঠিক উত্তরটি দ্রুত কমেন্টে জানিয়ে পুরস্কার জিতে নিন। 🎁"
    else:
        return "💎✨ অত্যন্ত গুরুত্বপূর্ণ পোস্ট! সবাই লাইক/রিঅ্যাক্ট দিয়ে সাপোর্ট করুন। 👍🔥"

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

# ==================== GROUP WELCOME & GOODBYE ====================
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

        welcome_text = (
            f"👑 **Hi {user_tag} welcome to {group_title}!** ✨\n\n"
            "🔥 আমাদের অফিশিয়াল চ্যানেলে সমস্ত আপডেট ও গিভঅ্যাওয়ে দেওয়া হয়। নিচে ক্লিক করে এখনি জয়েন করুন!"
        )
        channel_box_markup = types.InlineKeyboardMarkup(row_width=1)
        channel_box_markup.add(types.InlineKeyboardButton("💎 Official Telegram Channel ↗", url=REQ_CHANNEL_LINK))

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
    farewell_text = f"👋 **বিদায়, {user_tag}!**\n🚶 আপনি গ্রুপ ছেড়ে চলে গেলেন। আপনার ভবিষ্যৎ পথচলার জন্য শুভকামনা রইল! ✨"
    farewell_markup = types.InlineKeyboardMarkup(row_width=1)
    farewell_markup.add(types.InlineKeyboardButton("📢 অফিসিয়াল চ্যানেলে যুক্ত থাকুন ↗", url=REQ_CHANNEL_LINK))

    try:
        bot.send_message(message.chat.id, farewell_text, reply_markup=farewell_markup, parse_mode='Markdown')
    except Exception as e:
        print(f"Goodbye error: {e}")

# ==================== START & NAVIGATION ====================
@bot.callback_query_handler(func=lambda call: call.data == "verify_channel_sub")
def check_channel_verification(call):
    if is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ অভিনন্দন! আপনার ভেরিফিকেশন সফল হয়েছে।")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_welcome(call.message, call.from_user)
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি! আগে জয়েন করুন।", show_alert=True)

def send_welcome(message, user=None):
    u = user if user else message.from_user
    text = (
        f"🌹 **স্বাগতম, {u.first_name}!** 👋✨\n\n"
        "আমি আপনার অ্যাডভান্সড গ্রুপ ম্যানেজমেন্ট ও অটোমেশন রোবট — **Rafim Rose Manager**।\n\n"
        "🛡️ গ্রুপকে লিঙ্ক-স্প্যামারদের হাত থেকে রক্ষা করতে এবং স্মুথলি কন্ট্রোল করতে আমাকে আপনার গ্রুপে **Admin** হিসেবে যুক্ত করুন।"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_reply_keyboard(), parse_mode='Markdown')
    bot.send_message(message.chat.id, "⚡ **মডিউল ড্যাশবোর্ড:**\nনিচের যেকোনো মডিউলে ক্লিক করে বিস্তারিত দেখে নিন:", reply_markup=get_full_rose_dashboard(), parse_mode='Markdown')

@bot.message_handler(commands=['start', 'help'])
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
        bot.reply_to(message, "✅ বট সক্রিয় রয়েছে! সমস্ত মডিউল দেখতে ইনবক্সে /start দিন।")

@bot.callback_query_handler(func=lambda call: call.data.startswith("mod_") or call.data == "back_to_full_menu")
def handle_module_callbacks(call):
    if not is_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "⚠️ অনুগ্রহ করে আগে চ্যানেলে জয়েন করুন!", show_alert=True)
        return

    if call.data == "back_to_full_menu":
        bot.edit_message_text(
            "⚡ **মডিউল ড্যাশবোর্ড:**\nনিচের যেকোনো মডিউলে ক্লিক করে বিস্তারিত দেখে নিন:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=get_full_rose_dashboard(),
            parse_mode='Markdown'
        )
        return

    mod_key = call.data.replace("mod_", "")
    info_text = MODULE_DETAILS.get(mod_key, "📌 এই মডিউলটি সম্পূর্ণ সক্রিয় রয়েছে।")

    # স্ক্রিনশটের মতো নিচে Back to Menu এবং Support Admin বাটন শো করবে
    bot.edit_message_text(
        info_text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=get_module_nav_markup(),
        parse_mode='Markdown'
    )

# ==================== GROUP SMART RESPONDER & FILTERS ====================
def generate_group_smart_answer(text):
    t = text.lower() if text else ""
    if any(w in t for w in ["কেমন আছিস", "কেমন আছেন", "how are you"]):
        return "আলহামদুলিল্লাহ, আমি দারুণ আছি! আপনি কেমন আছেন? 😊✨"
    elif any(w in t for w in ["বট", "bot", "admin", "মালিক"]):
        return "আমি আপনাদের সহযোগিতায় সার্বক্ষণিক প্রস্তুত। ডেভেলপার ও ওনার: @rafimhossen 🛡️👑"
    elif any(w in t for w in ["সাহায্য", "help", "কমান্ড"]):
        return "যেকোনো তথ্যের জন্য বটের ইনবক্সে গিয়ে /start দিতে পারেন। 📌⚡"
    else:
        return "আপনার বার্তাটি লক্ষ্য করেছি! আলোচনা চালিয়ে যান। 👍💬"

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
        chats_cnt = len(get_all_chats())
        users_cnt = get_total_users()
        bot.reply_to(message, f"📊 **স্ট্যাটাস:** অনলাইন 🟢\n👥 মেম্বার ডেটা: {users_cnt} জন\n🌐 সক্রিয় গ্রুপ: {chats_cnt} টি\n⚡ পিং: অতি দ্রুত", parse_mode='Markdown')
    elif message.text == "📖 কমান্ড লিস্ট":
        bot.send_message(message.chat.id, "⚡ **মডিউল ড্যাশবোর্ড:**\nনিচের যেকোনো মডিউলে ক্লিক করে কমান্ড দেখে নিন:", reply_markup=get_full_rose_dashboard(), parse_mode='Markdown')
    elif message.text == "👤 আমার আইডি ও তথ্য":
        u = message.from_user
        bot.reply_to(message, f"👤 **তথ্য:**\n• নাম: {u.first_name}\n• ইউজারনেম: @{u.username or 'নাই'}\n• আইডি: `{u.id}`", parse_mode='Markdown')
    elif message.text == "🛡️ অ্যাডমিনগণ":
        bot.reply_to(message, "গ্রুপে গিয়ে `/admins` দিলে অ্যাডমিনদের তালিকা দেখা যাবে।")
    elif message.text == "📜 গ্রুপের নিয়ম":
        bot.reply_to(message, "📜 গ্রুপে কোনো লিঙ্ক, স্প্যাম বা খারাপ আচরণ সম্পূর্ণ নিষিদ্ধ।")
    elif message.text == "➕ গ্রুপে যুক্ত করুন":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("➕ Add Bot to Group ↗", url=f"https://t.me/{bot_info.username}?startgroup=true"))
        bot.send_message(message.chat.id, "গ্রুপে যুক্ত করতে চাপ দিন:", reply_markup=m)
    elif message.text == "📢 চ্যানেলে যুক্ত করুন":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("📢 Add Bot to Channel ↗", url=f"https://t.me/{bot_info.username}?startchannel=true"))
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
    print(f"Bot Online: @{bot_info.username}. Master Engine Loaded!", flush=True)

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Connection recovery: {e}", flush=True)
            time.sleep(3)
