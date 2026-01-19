import telebot
import json
import os
import datetime
import schedule
import time

# --- Глобальні налаштування бота та каналу ---
BOT_TOKEN = '8079778934:AAFBAQpsw7X8cnWWQ7jka2NvQ2jRCayeoo0'
CHANNEL_ID = '-1002919228474'
ADMIN_ID = 466172691  # Ваш Telegram ID
bot = telebot.TeleBot(BOT_TOKEN)

# --- Назви категорій постів та їх розклад ---
CATEGORIES = {
    'monday': 'Фінансова грамотність',
    'wednesday': 'Фінансовий захист',
    'friday': 'Державна підтримка'
}

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

def publish_next_post_by_category():
    """Публікує наступний пост з черги відповідно до категорії поточного дня."""
    posts_queue = load_posts_queue()
    today = datetime.datetime.now().strftime("%A").lower()

    today_category_key = ''
    if today == 'monday':
        today_category_key = 'monday'
    elif today == 'wednesday':
        today_category_key = 'wednesday'
    elif today == 'friday':
        today_category_key = 'friday'
    else:
        print("Сьогодні не день публікації за розкладом.")
        return

    post_to_publish = None
    post_index = -1
    for i, post in enumerate(posts_queue):
        if post.get('category') == today_category_key:
            post_to_publish = post
            post_index = i
            break

    if post_to_publish is None:
        print(f"Черга для категорії '{CATEGORIES[today_category_key]}' порожня.")
        bot.send_message(ADMIN_ID, f"⚠️ Черга для категорії **'{CATEGORIES[today_category_key]}'** порожня. Запланований пост не опубліковано.", parse_mode='Markdown')
        return

    posts_queue.pop(post_index)
    save_posts_queue(posts_queue)
    publish_post(post_to_publish, CHANNEL_ID, ADMIN_ID)

# --- Запуск планувальника ---
schedule.every().monday.at("10:00").do(publish_next_post_by_category)
schedule.every().wednesday.at("10:00").do(publish_next_post_by_category)
schedule.every().friday.at("10:00").do(publish_next_post_by_category)

while True:
    schedule.run_pending()
    time.sleep(1)