import os #задяки чому програма спілкується з ос (для зв'язку програми з Render)
import psycopg2 #база для роботи PostgreSQL
import threading # для багатозадачності (показує сайт і чекає повідомлення в Телеграмі)
from datetime import datetime # Для додавання дати створення
from flask import Flask, render_template, request, session, redirect, url_for, flash #скелет сайту
from werkzeug.security import generate_password_hash, check_password_hash #для прихованого паролю
from tgbot import bot #телеграм бот

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-123')
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection() # Відкриваємо з'єднання
    cur = conn.cursor() # "беремо ручку", щоб писати в базу
    
    # 1. Силою видаляємо стару таблицю (це очистить старі помилки)
    #cur.execute("DROP TABLE IF EXISTS users CASCADE;")
    
    # 2. Створюємо нову чисту таблицю
    cur.execute('''
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    ''')
    
    # 3. Створюємо адміна з паролем SuperSecret2026 (який у тебе на скріншоті)
    raw_password = os.environ.get('ADMIN_PASSWORD', 'default_password')
    hashed_pw = generate_password_hash(raw_password)
    cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", ('admin', hashed_pw))
    
    # 4. Перевіряємо таблицю skills (про всяк випадок)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            name TEXT PRIMARY KEY, 
            level TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    conn.commit() # Натискаємо "Зберегти"
    cur.close() # Кладемо ручку
    conn.close() # Кладемо слухавку
    print("!!! СИСТЕМА: БАЗА ДАНИХ ОЧИЩЕНА ТА СТВОРЕНА ЗАНОВО !!!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        name = request.form.get('user_name')
        msg = request.form.get('user_message')
        # Тут логіка відправки ботом
        bot.send_message(466172691, f"Нове повідомлення!\nВід: {name}\nТекст: {msg}")
        flash('Повідомлення надіслано!', 'success')
    return render_template('contacts.html', my_phone="096-079-59-95")

@app.route('/about', methods=['GET', 'POST'])
def about():
    conn = get_db_connection()
    cursor = conn.cursor()

    user_status = "Гість"

    if session.get('is_admin'):
        user_status = "Адміністратор (Євгеній)"
    
    if request.method == 'POST' and session.get('is_admin'):
        new_skill = request.form.get('skill_name')
        skill_to_delete = request.form.get('delete_skill')

        if new_skill:
            cursor.execute("INSERT INTO skills (name, level, created_at) VALUES (%s, %s, %s)", (new_skill, skill_level, datetime.now()))
            flash('Навичку додано!', 'success')
        
        if skill_to_delete:
            cursor.execute("DELETE FROM skills WHERE name = %s", (skill_to_delete,))
            flash('Навичку видалено!', 'success')
            
        conn.commit()

    cursor.execute("SELECT name, created_at FROM skills ORDER BY created_at DESC") #"Вибери дані з цих колонок у таблиці skills, Відсортуй їх так, щоб найновіші були зверху"
    skills_data = cursor.fetchall() # Забери все, що знайшов
    cursor.close()
    conn.close()
    return render_template('about.html', status=user_status, skills_list=skills_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cur = conn.cursor()
        # 1. Шукаємо користувача в базі
        cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        user_record = cur.fetchone()
        cur.close()
        conn.close()

        # 2. Перевіряємо: чи знайшли ми користувача і чи підходить пароль до хешу
        if user_record and check_password_hash(user_record[0], password):
            session['is_admin'] = True
            flash('Ви успішно увійшли!', 'success')
            return redirect(url_for('about'))
        else:
            flash('Невірний логін або пароль!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

# Запобіжник для бота: запускаємо лише в основному процесі Gunicorn
# КІНЕЦЬ ФАЙЛУ main.py

if __name__ == '__main__':
    # Цей блок працює, коли ти запускаєш код сам на комп'ютері
    init_db()
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True), daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
else:
    # Цей блок працює на Render (Gunicorn)
    init_db()
    # Запускаємо бота ТІЛЬКИ ТУТ і тільки один раз
    if not os.environ.get("WERKZEUG_RUN_MAIN"): 
        print("Запуск Telegram бота...")
        threading.Thread(target=lambda: bot.infinity_polling(none_stop=True), daemon=True).start()