from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    content TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists"
        conn.close()
        return redirect('/')
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password_hash(user[1], password):
        session['user_id'] = user[0]
        return redirect('/dashboard')
    return "Invalid credentials"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id, content FROM tasks WHERE user_id = ?", (session['user_id'],))
    tasks = c.fetchall()
    conn.close()
    return render_template('dashboard.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/')
    task = request.form['task']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, content) VALUES (?, ?)", (session['user_id'], task))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/delete/<int:task_id>')
def delete(task_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')
@app.route('/edit/<int:task_id>', methods=['POST'])
def edit(task_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    updated_task = request.form['updated_task']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET content = ? WHERE id = ? AND user_id = ?", (updated_task, task_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect('/dashboard')
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Get username
    c.execute("SELECT username FROM users WHERE id = ?", (session['user_id'],))
    username = c.fetchone()[0]

    # Count tasks
    c.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?", (session['user_id'],))
    task_count = c.fetchone()[0]

    conn.close()

    return render_template("profile.html", username=username, task_count=task_count)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
