import os
import psycopg2
import threading
from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from tgbot import bot 

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-123')
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS skills (id SERIAL PRIMARY KEY, name TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)')
        hashed_pw = generate_password_hash('1234')
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING', ('admin', hashed_pw))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Помилка БД: {e}")

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
            cursor.execute("INSERT INTO skills (name) VALUES (%s)", (new_skill,))
            conn.commit()
    cursor.execute("SELECT name FROM skills")
    skills = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return render_template('about.html', name="Євген", phone="0960795995", skills_list=skills)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == '1234':
            session['is_admin'] = True
            return redirect(url_for('about'))
    return render_template('login.html')

def run_bot():
    bot.infinity_polling(none_stop=True)

# Запуск всього разом
init_db()
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
