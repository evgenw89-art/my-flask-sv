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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Витягуємо назву та дату (так само, як на сайті)
    cursor.execute("SELECT name, created_at FROM skills ORDER BY created_at DESC")
    skills_data = cursor.fetchall()
    
    cursor.close()
    conn.close()

    if not skills_data:
        bot.send_message(message.chat.id, "📜 Список навичок порожній.")
        return

    # Формуємо гарний текст повідомлення
    response = "🚀 *Мої навички:*\n\n"
    for skill in skills_data:
        name = skill[0]
        # Форматуємо дату (якщо вона є)
        date_str = skill[1].strftime('%d.%m.%Y') if skill[1] else "раніше"
        response += f"✅ {name} _(додано: {date_str})_\n"

    bot.send_message(message.chat.id, response, parse_mode="Markdown")

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
