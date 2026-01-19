import telebot
import json
import os
import psycopg2 

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Глобальні налаштування бота ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
# Беремо посилання з Render, або локальне, якщо працюємо вдома
DATABASE_URL = os.environ.get('DATABASE_URL')
CHANNEL_ID = '-1002919228474'
ADMIN_ID = 466172691  
bot = telebot.TeleBot(BOT_TOKEN)

# --- Стан та категорії ---
user_states = {}
user_data = {}
CATEGORIES = {
    'monday': 'Фінансова грамотність',
    'wednesday': 'Фінансовий захист',
    'friday': 'Державна підтримка'
}

def get_db_connection():
    # Важливо: sslmode='require' обов'язковий для Render PostgreSQL
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def is_admin(user_id):
    return user_id == ADMIN_ID

# ... (тут твої функції створення клавіатур та роботи з чергою постів залишаються без змін) ...

@bot.message_handler(commands=['start', 'admin'])
def handle_start(message):
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "Привіт, адміністраторе! Обери дію:", reply_markup=create_admin_keyboard())
    else:
        bot.send_message(message.chat.id, "Вибачте, ви не адміністратор.")

@bot.message_handler(commands=['skills'])
def show_skills(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Ця команда доступна тільки адміністратору.")
        return

    # ВИПРАВЛЕНО: тепер використовуємо PostgreSQL
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM skills')
        skills = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if skills:
            reply = "🛠 Мої навички з сайту:\n" + "\n".join([f"- {s[0]}" for s in skills])
        else:
            reply = "Список навичок поки порожній."
    except Exception as e:
        reply = f"❌ Помилка бази даних: {e}"
    
    bot.reply_to(message, reply)

@bot.message_handler(commands=['add'])
def add_skill_via_bot(message):
    if not is_admin(message.from_user.id): return
    
    skill_name = message.text.replace('/add ', '').strip()
    if not skill_name or skill_name == '/add':
        bot.reply_to(message, "Напиши: /add Назва")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # %s для PostgreSQL
        cursor.execute('INSERT INTO skills (name) VALUES (%s)', (skill_name,))
        conn.commit()
        cursor.close()
        conn.close()
        bot.reply_to(message, f"✅ Навичку '{skill_name}' додано в PostgreSQL!")
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {e}")

# ... (решта коду для callback_query_handler та handle_post_text) ...

if __name__ == "__main__":
    print("Бот запустився через tgbot.py...")
    bot.infinity_polling(none_stop=True)