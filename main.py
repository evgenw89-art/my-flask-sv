import os
import psycopg2
import threading
from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from tgbot import bot
from datetime import datetime 

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_secret_123')

# Отримуємо URL бази з Render
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    # Використовуємо PostgreSQL (як у боті)
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    """Створюємо таблиці в PostgreSQL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS skills (id SERIAL PRIMARY KEY, name TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)')
        # Додає колонку created_at, якщо вона ще не існує
        cursor.execute('ALTER TABLE skills ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        # Адмін за замовчуванням (пароль 1234)
        hashed_pw = generate_password_hash('1234')
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING', ('admin', hashed_pw))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Помилка ініціалізації БД: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about', methods=['GET', 'POST'])
def about():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST' and session.get('is_admin'):
        new_skill = request.form.get('skill_name')
        if new_skill:
            now = datetime.now()
            cursor.execute("INSERT INTO skills (name) VALUES (%s)", (new_skill, now))
            conn.commit()
            
    cursor.execute("SELECT name, created_at FROM skills ORDER BY created_at DESC")
    # Тепер fetchall() поверне список кортежів: [('Python', '2024-01-20 12:00'), ...]
    skills_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('about.html', name="Євген", phone="0960795995", skills_list=skills_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == '1234': # Для спрощення
            session['is_admin'] = True
            return redirect(url_for('about'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

def run_bot():
    bot.infinity_polling(none_stop=True)

# Запуск бази та бота перед стартом Flask
init_db()
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)