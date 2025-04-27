from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
DATABASE = 'database.db'

# 初始管理员凭证（可修改）
ADMIN_CREDENTIALS = {
    'admin': generate_password_hash('admin_password')
}

# 初始化数据库：用户表与图书表
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # 学生用户表
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    # 图书表
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            call_number TEXT PRIMARY KEY,
            title TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# 学生注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        student_id = request.form['id']
        pwd = request.form['password']
        hashed = generate_password_hash(pwd)
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO students (id, password) VALUES (?, ?)", (student_id, hashed))
            conn.commit()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('该ID已存在')
        finally:
            conn.close()
    return render_template('register.html')

# 登录（学生或管理员）
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['id']
        pwd = request.form['password']
        # 管理员登录检查
        if user_id in ADMIN_CREDENTIALS and check_password_hash(ADMIN_CREDENTIALS[user_id], pwd):
            session['user'] = user_id
            session['role'] = 'admin'
            return redirect(url_for('admin'))
        # 学生登录检查
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT password FROM students WHERE id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[0], pwd):
            session['user'] = user_id
            session['role'] = 'student'
            return redirect(url_for('search'))
        flash('用户名或密码错误')
    return render_template('login.html')

# 学生书籍搜索
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user' not in session or session.get('role') != 'student':
        return redirect(url_for('login'))
    books = []
    if request.method == 'POST':
        keyword = request.form['keyword']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute(
            "SELECT call_number, title FROM books WHERE title LIKE ? OR call_number LIKE ?",
            ('%'+keyword+'%', '%'+keyword+'%')
        )
        books = c.fetchall()
        conn.close()
    return render_template('search.html', books=books)

# 管理员图书管理
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    if request.method == 'POST':
        action = request.form['action']
        call_number = request.form['call_number']
        title = request.form['title']
        if action == 'add':
            c.execute("INSERT OR IGNORE INTO books (call_number, title) VALUES (?, ?)",
                      (call_number, title))
        elif action == 'delete':
            c.execute("DELETE FROM books WHERE call_number = ?", (call_number,))
        elif action == 'edit':
            c.execute("UPDATE books SET title = ? WHERE call_number = ?", (title, call_number))
        conn.commit()
    c.execute("SELECT call_number, title FROM books")
    all_books = c.fetchall()
    conn.close()
    return render_template('admin.html', books=all_books)

# 注销
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()           # 手动创建/检查数据库表
    app.run(debug=True) # 启动应用