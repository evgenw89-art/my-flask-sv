import telebot
import json
import os
import psycopg2 # Замість sqlite3

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- Глобальні налаштування бота та каналу ---
# Тепер Python сам візьме токен із налаштувань Render
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DATABASE_URL = os.environ.get('DATABASE_URL')
CHANNEL_ID = '-1002919228474'
ADMIN_ID = 466172691  # Ваш Telegram ID
bot = telebot.TeleBot(BOT_TOKEN)

# --- Глобальні змінні для стану ---
user_states = {}
user_data = {}

# --- Назви категорій постів та їх розклад ---
CATEGORIES = {
    'monday': 'Фінансова грамотність',
    'wednesday': 'Фінансовий захист',
    'friday': 'Державна підтримка'
}

# Отримуємо URL бази даних з налаштувань сервера (або використовуємо локальну для тесту)
DATABASE_URL = os.environ.get('DATABASE_URL', 'тут_твій_external_url_з_render')

def get_db_connection():
    # PostgreSQL використовує інший метод підключення
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

# --- Допоміжні функції ---
def is_admin(user_id):
    """Перевіряє, чи є користувач адміністратором."""
    return user_id == ADMIN_ID

def create_admin_keyboard():
    """Створює клавіатуру для адмін-панелі."""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Опублікувати зараз", callback_data="publish_now"))
    markup.add(InlineKeyboardButton("Додати пост", callback_data="add_post"))
    markup.add(InlineKeyboardButton("Переглянути чергу", callback_data="view_queue"))
    return markup

def create_category_keyboard():
    """Створює клавіатуру для вибору категорії."""
    markup = InlineKeyboardMarkup()
    for key, value in CATEGORIES.items():
        markup.add(InlineKeyboardButton(value, callback_data=f"select_category_{key}"))
    markup.add(InlineKeyboardButton("Назад до адмін-панелі", callback_data="back_to_admin"))
    return markup

# --- Функції для роботи з чергою постів ---
def load_posts_queue():
    """Завантажує чергу постів з файлу."""
    if os.path.exists("posts_to_publish.json"):
        with open("posts_to_publish.json", "r", encoding="utf-8") as f:
            try:
                data = f.read()
                return json.loads(data) if data else []
            except json.JSONDecodeError:
                print("Помилка читання posts_to_publish.json. Файл пошкоджений.")
                return []
    return []

def save_posts_queue(posts):
    """Зберігає чергу постів у файл."""
    with open("posts_to_publish.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

def publish_post(post_to_publish, channel_id, admin_id):
    """Надсилає пост без зображення."""
    try:
        category_name = CATEGORIES.get(post_to_publish.get('category'), 'Без категорії')
        post_text = f"**{category_name}**\n\n{post_to_publish['text']}"
        bot.send_message(channel_id, post_text, parse_mode='Markdown')

        print(f"Опубліковано пост з категорії '{category_name}'.")
        bot.send_message(admin_id, f"✅ Опубліковано новий пост з категорії **{category_name}**.", parse_mode='Markdown')
    except Exception as e:
        print(f"Виникла помилка під час публікації посту: {e}")
        bot.send_message(admin_id, f"❌ Виникла помилка під час публікації: {e}")

def publish_next_post_by_category_now(category_key):
    """Публікує наступний пост з черги для конкретної категорії."""
    posts_queue = load_posts_queue()

    post_to_publish = None
    post_index = -1
    for i, post in enumerate(posts_queue):
        if post.get('category') == category_key:
            post_to_publish = post
            post_index = i
            break

    if post_to_publish is None:
        bot.send_message(ADMIN_ID, f"У цій категорії немає постів.")
        return

    posts_queue.pop(post_index)
    save_posts_queue(posts_queue)
    publish_post(post_to_publish, CHANNEL_ID, ADMIN_ID)

# --- Обробники команд та кнопок ---
@bot.message_handler(commands=['start', 'admin'])
def handle_start(message):
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "Привіт, адміністраторе! Обери дію:", reply_markup=create_admin_keyboard())
    else:
        bot.send_message(message.chat.id, "Вибачте, ви не адміністратор.")

@bot.message_handler(commands=['skills'])
def show_skills(message):
    # Перевіряємо, чи це ти
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "Ця команда доступна тільки адміністратору.")
        return

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM skills')
    skills = cursor.fetchall()
    conn.close()
    
    if skills:
        reply = "🛠 Мої навички з сайту:\n" + "\n".join([f"- {s[0]}" for s in skills])
    else:
        reply = "Список навичок поки порожній."
    
    bot.reply_to(message, reply)

@bot.message_handler(commands=['add'])
def add_skill_via_bot(message):
    if not is_admin(message.from_user.id): return
    
    skill_name = message.text.replace('/add ', '').strip()
    
    conn = get_db_connection() # Викликаємо наше нове підключення
    cursor = conn.cursor()
    # УВАГА: %s замість ?
    cursor.execute('INSERT INTO skills (name) VALUES (%s)', (skill_name,))
    conn.commit()
    cursor.close()
    conn.close()
    
    bot.reply_to(message, f"✅ Навичку '{skill_name}' додано в PostgreSQL!")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "Доступ заборонено.")
        return

    if call.data == "publish_now":
        posts_queue = load_posts_queue()
        markup = InlineKeyboardMarkup()
        for key, value in CATEGORIES.items():
            count = sum(1 for post in posts_queue if post.get('category') == key)
            if count > 0:
                markup.add(InlineKeyboardButton(f"{value} ({count})", callback_data=f"publish_now_from_{key}"))

        if not markup.keyboard:
            bot.send_message(call.message.chat.id, "Немає постів у черзі для публікації.")
            return

        bot.send_message(call.message.chat.id, "Оберіть категорію, з якої бажаєте опублікувати пост:", reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("publish_now_from_"):
        category_key = call.data.replace("publish_now_from_", "")
        publish_next_post_by_category_now(category_key)
        bot.answer_callback_query(call.id, "Пост опубліковано!")

    elif call.data == "add_post":
        bot.edit_message_text("Оберіть категорію для нового посту:", call.message.chat.id, call.message.message_id, reply_markup=create_category_keyboard())
        user_states[call.from_user.id] = 'awaiting_category'
        bot.answer_callback_query(call.id)

    elif call.data.startswith("select_category_"):
        category_key = call.data.replace("select_category_", "")
        user_states[call.from_user.id] = 'awaiting_post_text'
        user_data[call.from_user.id] = {'category': category_key}
        bot.edit_message_text(f"Ви обрали категорію **'{CATEGORIES[category_key]}'**. Тепер надішліть текст посту.", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data == "view_queue":
        posts_queue = load_posts_queue()
        if not posts_queue:
            message_text = "Черга публікацій порожня."
        else:
            message_text = "**Пости в черзі:**\n"
            for i, post in enumerate(posts_queue):
                category_name = CATEGORIES.get(post['category'], 'Без категорії')
                message_text += f"\n**{i + 1}.** Категорія: *{category_name}*\n"
                message_text += f"Текст: `{post['text'][:50]}...`\n"
        bot.edit_message_text(message_text, call.message.chat.id, call.message.message_id, reply_markup=create_admin_keyboard(), parse_mode='Markdown')
        bot.answer_callback_query(call.id)

    elif call.data == "back_to_admin":
        bot.edit_message_text("Повертаємося до адмін-панелі:", call.message.chat.id, call.message.message_id, reply_markup=create_admin_keyboard())
        bot.answer_callback_query(call.id)

# --- Обробник текстових повідомлень ---
@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and user_states.get(message.from_user.id) == 'awaiting_post_text')
def handle_post_text(message):
    user_id = message.from_user.id
    if user_id in user_data:
        posts_queue = load_posts_queue()
        post_data = {
            'text': message.text,
            'category': user_data[user_id]['category']
        }
        posts_queue.append(post_data)
        save_posts_queue(posts_queue)

        user_states.pop(user_id, None)
        user_data.pop(user_id, None)

        bot.send_message(message.chat.id, f"✅ Пост успішно додано до черги у категорію **'{CATEGORIES[post_data['category']]}'**.", reply_markup=create_admin_keyboard(), parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id, "Виникла помилка. Спробуйте почати знову, натиснувши /admin.")

print("Бот запущено і готовий до роботи...")
bot.infinity_polling(none_stop=True)