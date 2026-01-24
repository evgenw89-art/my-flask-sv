import os
import psycopg2
import threading
from datetime import datetime
from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from tgbot import bot
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-123')
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Крок А: Створюємо таблицю навичок (вона у тебе вже є, просто перевіряємо)
    cur.execute('CREATE TABLE IF NOT EXISTS skills (name TEXT PRIMARY KEY, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);')
    
    # Крок Б: Створюємо нову таблицю для користувачів
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    ''')
    
    # Крок В: Перевіряємо, чи є вже адмін у базі
    cur.execute("SELECT * FROM users WHERE username = 'admin';")
    admin_exists = cur.fetchone()
    
    # Крок Г: Якщо адміна немає — створюємо його
    if not admin_exists:
        hashed_pw = generate_password_hash('твій_пароль_тут') # Заміни на свій!
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", ('admin', hashed_pw))
        print("Система: Таблиця створена, адмін доданий!")
    
    conn.commit()
    cur.close()
    conn.close()

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

    if request.method == 'POST' and session.get('is_admin'):
        new_skill = request.form.get('skill_name')
        skill_to_delete = request.form.get('delete_skill')

        if new_skill:
            cursor.execute("INSERT INTO skills (name, created_at) VALUES (%s, %s)", (new_skill, datetime.now()))
            flash('Навичку додано!', 'success')
        
        if skill_to_delete:
            cursor.execute("DELETE FROM skills WHERE name = %s", (skill_to_delete,))
            flash('Навичку видалено!', 'success')
            
        conn.commit()

    cursor.execute("SELECT name, created_at FROM skills ORDER BY created_at DESC")
    skills_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('about.html', name="Євгеній Петров", phone="0960795995", skills_list=skills_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == '1234':
            session['is_admin'] = True
            return redirect(url_for('about'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))

# Запобіжник для бота: запускаємо лише в основному процесі Gunicorn
if __name__ == '__main__':
    init_db()
    threading.Thread(target=lambda: bot.infinity_polling(none_stop=True), daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
else:
    # Це спрацює на Render (Gunicorn)
    init_db()
    # Щоб уникнути конфлікту 409, бот на Render краще запускати окремо, 
    # але для навчання лишаємо тут з daemon=True
    if not os.environ.get("WERKZEUG_RUN_MAIN"): 
        threading.Thread(target=lambda: bot.infinity_polling(none_stop=True), daemon=True).start()