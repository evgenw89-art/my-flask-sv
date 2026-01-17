import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)


def init_db():
    # Підключаємося до файлу бази даних (він створиться сам)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Створюємо таблицю skills, якщо її не існує
    # Столбець id - унікальний номер, name - назва навички
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# Викликаємо ініціалізацію при запуску
init_db()


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