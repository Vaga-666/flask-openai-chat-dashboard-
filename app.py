import logging
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
from dotenv import load_dotenv
import os

# Загружаем переменные из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    filename="error.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

# Настройка Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Настройка OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Модели базы данных
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)

    user = db.relationship('User', backref='chats')


class ChatSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    max_tokens = db.Column(db.Integer, default=50)

# Создание таблиц
with app.app_context():
    db.create_all()

# Получение ответа от OpenAI
def get_ai_response(message, max_tokens):
    try:
        logging.info(f"GPT-3.5 turbo запрос: {message} (max_tokens={max_tokens})")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": message}
            ],
            max_tokens=max_tokens
        )
        result = response.choices[0].message.content.strip()
        logging.info(f"GPT ответ: {result}")
        return result
    except Exception as e:
        logging.error(f"Ошибка OpenAI: {str(e)}", exc_info=True)
        return f"[Ошибка AI: {str(e)}]"

# Главная
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))

        user = User(username=username, password=password)
        db.session.add(user)
        try:
            db.session.commit()
            flash('Регистрация успешна! Войдите в систему.')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Ошибка при регистрации: {str(e)}")
            flash('Ошибка регистрации. Попробуйте позже.')
            return redirect(url_for('register'))

        return redirect(url_for('login'))
    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        flash('Неверное имя пользователя или пароль.')
    return render_template('login.html')

# Выход
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    username = session.get('username', 'Аноним')

    settings = ChatSettings.query.filter_by(user_id=user_id).first()
    if not settings:
        settings = ChatSettings(user_id=user_id, max_tokens=50)
        db.session.add(settings)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Ошибка при создании настроек: {str(e)}")

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'chat':
            message = request.form.get('message', '').strip()
            if message:
                response = get_ai_response(message, settings.max_tokens)
                chat = ChatHistory(user_id=user_id, message=message, response=response)
                db.session.add(chat)
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Ошибка при сохранении чата: {str(e)}")
                    flash("Ошибка при сохранении сообщения.")
            else:
                flash("Сообщение не может быть пустым.")

        elif action == 'settings':
            try:
                new_tokens = int(request.form['max_tokens'])
                settings.max_tokens = new_tokens
                db.session.commit()
                flash('Настройки обновлены.')
            except Exception as e:
                db.session.rollback()
                logging.error(f"Ошибка при обновлении настроек: {str(e)}")
                flash('Ошибка при обновлении настроек.')

    # 📌 История только для текущего пользователя:
    history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.id).all()

    return render_template('dashboard.html', history=history, settings=settings)


# Запуск
if __name__ == '__main__':
    if os.path.exists("chat.db"):
        os.remove("chat.db")
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="127.0.0.1", port=5000)
