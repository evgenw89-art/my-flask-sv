import telebot
import json
import os
import psycopg2 
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Налаштування (Беремо все з Render) ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DATABASE_URL = os.environ.get('DATABASE_URL')
CHANNEL_ID = '-1002919228474'
ADMIN_ID = 466172691  

bot = telebot.TeleBot(BOT_TOKEN)

# --- Категорії ---
CATEGORIES = {
    'monday': 'Фінансова грамотність',
    'wednesday': 'Фінансовий захист',
    'friday': 'Державна підтримка'
}

def get_db_connection():
    # Обов'язково додаємо sslmode для безпечного з'єднання з Render
    return psycopg2.connect(DATABASE_URL, sslmode='require')

# --- Функція перевірки адміна ---
def is_admin(user_id):
    return user_id == ADMIN_ID

# --- Оновлені команди для роботи з PostgreSQL ---

@bot.message_handler(commands=['skills'])
def show_skills(message):
    if not is_admin(message.from_user.id): return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM skills')
        skills = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if skills:
            reply = "🛠 Навички з бази PostgreSQL:\n" + "\n".join([f"- {s[0]}" for s in skills])
        else:
            reply = "Список порожній."
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка бази: {e}")

@bot.message_handler(commands=['add'])
def add_skill_via_bot(message):
    if not is_admin(message.from_user.id): return
    
    skill_name = message.text.replace('/add ', '').strip()
    if not skill_name or skill_name == '/add':
        bot.reply_to(message, "Напиши так: /add Текст навички")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # %s — це стандарт для psycopg2 (замість ?)
        cursor.execute('INSERT INTO skills (name) VALUES (%s)', (skill_name,))
        conn.commit()
        cursor.close()
        conn.close()
        bot.reply_to(message, f"✅ Навичку '{skill_name}' додано!")
    except Exception as e:
        bot.reply_to(message, f"❌ Помилка: {e}")

# --- Решту твого коду з клавіатурами та постами можна залишати нижче ---
# (Але пам'ятайте про тимчасовість JSON-файлів на Render)
