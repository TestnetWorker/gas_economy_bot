import telebot
import sqlite3
import random
import os

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("Переменная BOT_TOKEN не задана в Railway Variables")

bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("gas.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    gc INTEGER DEFAULT 0
)
""")
conn.commit()

def get_user(user_id, username):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, username, gc) VALUES (?, ?, 0)", (user_id, username))
        conn.commit()

def add_gc(user_id, username, amount):
    get_user(user_id, username)
    cursor.execute("UPDATE users SET gc = gc + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

def get_balance(user_id):
    cursor.execute("SELECT gc FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 0

@bot.message_handler(commands=['start'])
def start(message):
    username = message.from_user.username or message.from_user.first_name
    get_user(message.from_user.id, username)
    bot.reply_to(message, "💨 GAS ECONOMY ONLINE\n\n/balance\n/top\n/roulette 50")

@bot.message_handler(commands=['balance'])
def balance(message):
    gc = get_balance(message.from_user.id)
    bot.reply_to(message, f"💰 Баланс: {gc} GC")

@bot.message_handler(commands=['top'])
def top(message):
    cursor.execute("SELECT username, gc FROM users ORDER BY gc DESC LIMIT 10")
    users = cursor.fetchall()
    text = "🏆 ТОП ГАЗА\n\n"
    for i, (name, gc) in enumerate(users, 1):
        text += f"{i}. @{name} — {gc} GC\n"
    bot.reply_to(message, text)

@bot.message_handler(content_types=['voice'])
def voice_reward(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    add_gc(user_id, username, 5)
    bot.reply_to(message, "💨 +5 GC")

@bot.message_handler(commands=['roulette'])
def roulette(message):
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "Использование: /roulette 50")
        return
    try:
        amount = int(args[1])
    except:
        return
    user_id = message.from_user.id
    if get_balance(user_id) < amount:
        bot.reply_to(message, "❌ Недостаточно GC")
        return
    cursor.execute("UPDATE users SET gc = gc - ? WHERE user_id=?", (amount, user_id))
    outcomes = [0, 0.5, 1, 2, 5]
    weights = [40, 30, 15, 10, 5]
    multiplier = random.choices(outcomes, weights=weights)[0]
    win = int(amount * multiplier)
    username = message.from_user.username or message.from_user.first_name
    add_gc(user_id, username, win)
    bot.reply_to(message, f"🎰 x{multiplier}\n💰 {win} GC")

if __name__ == "__main__":
    print("Бот запущен")
    bot.infinity_polling()
