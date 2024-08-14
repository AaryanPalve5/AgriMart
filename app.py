from flask import Flask, request, render_template, redirect, url_for, send_file, session
import sqlite3
import io
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

login_manager = LoginManager()
login_manager.init_app(app)

def get_db_connection():
    conn = sqlite3.connect('images.db')
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'])
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            return 'Username already exists!'
        finally:
            conn.close()
        
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'])
            login_user(user_obj)
            return redirect(url_for('upload'))
        return 'Invalid credentials!'

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image'].read()
        supplier_name = request.form['supplier_name']
        company_contact = request.form['company_contact']
        user_id = current_user.id

        conn = get_db_connection()
        conn.execute("INSERT INTO images (name, description, price, image, supplier_name, company_contact, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (name, description, price, image, supplier_name, company_contact, user_id))
        conn.commit()
        conn.close()

        return redirect(url_for('gallery'))

    return render_template('upload.html')

@app.route('/gallery', methods=['GET', 'POST'])
def gallery():
    search_query = request.form.get('search', '')
    conn = get_db_connection()
    
    if search_query:
        images = conn.execute("SELECT id, name, description, price, supplier_name, company_contact FROM images WHERE name LIKE ?", 
                              ('%' + search_query + '%',)).fetchall()
    else:
        images = conn.execute("SELECT id, name, description, price, supplier_name, company_contact FROM images").fetchall()
    
    conn.close()
    
    return render_template('gallery.html', images=images, search_query=search_query)

@app.route('/image/<int:image_id>')
def image(image_id):
    conn = get_db_connection()
    img = conn.execute("SELECT image FROM images WHERE id = ?", (image_id,)).fetchone()
    conn.close()

    return send_file(io.BytesIO(img['image']), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=True)

#