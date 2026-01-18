import sqlite3
from flask import Flask, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, redirect, url_for
from flask import flash # Додай це до імпортів


app = Flask(__name__)
app.secret_key = 'super-secret-key-donot-share' # У реальних проєктах тут складний набір символів


def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Таблиця навичок (вже є)
    cursor.execute('CREATE TABLE IF NOT EXISTS skills (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)')
    
    # НОВА ТАБЛИЦЯ: Користувачі
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    # Створимо тестового адміна, якщо його ще немає
    # Пароль "1234" перетвориться на довгий нечитабельний код (хеш)
    hashed_password = generate_password_hash('1234')
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', hashed_password))
    except sqlite3.IntegrityError:
        pass # Адмін уже існує
        
    conn.commit()
    conn.close()

# Викликаємо ініціалізацію при запуску
init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[0], password):
            session['is_admin'] = True  # Помічаємо в сесії, що користувач - адмін
            flash('Ви успішно увійшли!', 'success') # Повідомлення про успіх
            return redirect(url_for('about'))
        else:
            flash('Невірний логін або пароль!', 'error') # Повідомлення про помилку
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('is_admin', None) # Видаляємо статус адміна
    return redirect(url_for('about'))

# Функція для завантаження даних із файлу
def load_skills():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # ТУТ ЗАВДАННЯ: напиши запит, щоб вибрати всі імена (name) з таблиці skills
    cursor.execute("SELECT name FROM skills")
    
    # Отримуємо всі результати. fetchall() повертає список кортежів [('Python',), ('Flask',)]
    rows = cursor.fetchall()
    conn.close()
    
    # Перетворюємо список кортежів у звичайний список рядків
    return [row[0] for row in rows]

# Функція для збереження даних у файл
def add_skill_db(skill_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # ТУТ ЗАВДАННЯ: напиши запит INSERT для додавання skill_name
    cursor.execute("INSERT INTO skills (name) VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def delete_skill_db(skill_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skills WHERE name = ?", (skill_name,))
    conn.commit()
    conn.close()    

@app.route('/about', methods=['GET', 'POST'])
def about():
    if request.method == 'POST':
        new_skill = request.form.get('skill_name')
        skill_to_delete = request.form.get('delete_skill')

        if new_skill:
            add_skill_db(new_skill)
            
        elif skill_to_delete:
            delete_skill_db(skill_to_delete)

    skills = load_skills()

    return render_template('about.html',
                           name="Євген",
                           phone="0960795995",
                           skills_list=skills)              
            
    
if __name__ == '__main__':
    app.run(debug=True)