import telebot
import google.generativeai as genai
import os
import threading
from flask import Flask

BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_KEY')

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(BOT_TOKEN)
users = {}

# Flask app для health check
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot is running", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# Запускаем Flask в отдельном потоке, чтобы не блокировать бота
threading.Thread(target=run_flask, daemon=True).start()

# Остальная логика бота (твоя)
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.chat.id
    users[uid] = {'messages_left': 10, 'premium': False}
    bot.reply_to(message, "🤖 10 бесплатных сообщений. /unlock - тест")

@bot.message_handler(commands=['unlock'])
def unlock(message):
    uid = message.chat.id
    users[uid] = {'messages_left': 999999, 'premium': True}
    bot.reply_to(message, "✅ Премиум активирован")

@bot.message_handler(func=lambda m: True)
def ai_reply(message):
    uid = message.chat.id
    if uid not in users:
        users[uid] = {'messages_left': 10, 'premium': False}
    if not users[uid]['premium'] and users[uid]['messages_left'] <= 0:
        bot.reply_to(message, "🔒 Бесплатные кончились. /unlock")
        return
    text = message.text
    if not users[uid]['premium']:
        bad = ['секс', 'порно', 'эротика', 'голый', '18+']
        if any(w in text.lower() for w in bad):
            bot.reply_to(message, "🚫 Купи премиум /unlock")
            return
    try:
        response = model.generate_content(text)
        answer = response.text
    except Exception as e:
        answer = f"Ошибка: {str(e)}"
    if not users[uid]['premium']:
        users[uid]['messages_left'] -= 1
        bot.reply_to(message, f"{answer}\n\nОсталось: {users[uid]['messages_left']}")
    else:
        bot.reply_to(message, answer)

print("✅ Бот запущен")
bot.infinity_polling()