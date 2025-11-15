# Все маршруты приложения - полная версия с анонимным голосованием
from flask import render_template, request, redirect, url_for, flash, session
import functools
from app.db.raw_connection import connect

app = None


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get('loggedin') is None:
            return redirect(url_for('login'))
        return view(**kwargs)

    return wrapped_view


def register_routes(flask_app):
    global app
    app = flask_app

    # Главная страница - список опросов
    @app.route("/")
    def index():
        conn = connect()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.id, s.title, s.description, s.created_by, s.created_at, s.is_anonymous, u.user_name 
                FROM surveys s 
                LEFT JOIN users u ON s.created_by = u.id 
                ORDER BY s.created_at DESC
            """)
            surveys = cursor.fetchall()
        return render_template('surveys.html', all_surveys=surveys)

    # Регистрация
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            user_name = request.form['user_name']
            password = request.form['password']
            print(f"DEBUG: Registration attempt - Username: '{user_name}', Password: '{password}'")

            conn = connect()
            with conn.cursor() as cursor:
                try:
                    # Проверяем, нет ли уже такого пользователя
                    cursor.execute("SELECT id FROM users WHERE user_name = %s", (user_name,))
                    existing = cursor.fetchone()
                    print(f"DEBUG: Existing user check: {existing}")

                    if existing:
                        flash('Username already exists! Please choose another.')
                        return render_template('registration.html')

                    # СОЗДАЕМ ПОЛЬЗОВАТЕЛЯ
                    print("DEBUG: Creating new user...")
                    cursor.execute(
                        "INSERT INTO users (user_name, password) VALUES (%s, %s)",
                        (user_name, password)
                    )
                    conn.commit()
                    print(f"DEBUG: User '{user_name}' created successfully!")

                    # ПРОВЕРЯЕМ что пользователь создался
                    cursor.execute("SELECT id, user_name FROM users WHERE user_name = %s", (user_name,))
                    created_user = cursor.fetchone()
                    print(f"DEBUG: Verification - Created user: {created_user}")

                    flash('Registration successful! Please login with your credentials.')
                    return redirect(url_for('login'))

                except Exception as e:
                    print(f"DEBUG: Registration ERROR: {e}")
                    flash(f'Registration error: {e}')
                    conn.rollback()

        return render_template('registration.html')

    # Вход
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user_name = request.form['user_name']
            password = request.form['password']
            print(f"DEBUG: Login attempt - Username: '{user_name}', Password: '{password}'")

            conn = connect()
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_name, password FROM users WHERE user_name = %s",
                    (user_name,)
                )
                user = cursor.fetchone()

            if user:
                print(f"DEBUG: User found - ID: {user[0]}, Username: '{user[1]}', Password in DB: '{user[2]}'")
                print(f"DEBUG: Password match: {user[2] == password}")
            else:
                print(f"DEBUG: User '{user_name}' NOT FOUND in database")

            if user and user[2] == password:
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['loggedin'] = True
                print(f"DEBUG: Login SUCCESSFUL for {user_name}")
                return redirect(url_for('index'))
            else:
                print(f"DEBUG: Login FAILED for {user_name}")
                flash('Incorrect username or password!')

        return render_template('login.html')

    # Выход
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # Создание опроса
    @app.route('/create-survey', methods=['GET', 'POST'])
    @login_required
    def create_survey():
        if request.method == 'POST':
            title = request.form['title']
            description = request.form['description']
            is_anonymous = bool(request.form.get('is_anonymous', False))
            created_by = session.get('user_id')

            conn = connect()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO surveys (title, description, created_by, is_anonymous) VALUES (%s, %s, %s, %s) RETURNING id",
                    (title, description, created_by, is_anonymous)
                )
                survey_id = cursor.fetchone()[0]
                conn.commit()

            flash('Survey created successfully! Add options')
            return redirect(url_for('add_option', survey_id=survey_id))

        return render_template('create_survey.html')

    # Просмотр опроса
    @app.route('/survey/<int:survey_id>')
    def get_survey(survey_id):
        conn = connect()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.id, s.title, s.description, s.created_by, s.created_at, s.is_anonymous, u.user_name 
                FROM surveys s 
                LEFT JOIN users u ON s.created_by = u.id 
                WHERE s.id = %s
            """, (survey_id,))
            survey = cursor.fetchone()

            cursor.execute(
                "SELECT id, description FROM options WHERE survey_id = %s",
                (survey_id,)
            )
            options = cursor.fetchall()

            # Проверяем, голосовал ли пользователь (по user_id или IP)
            user_voted = False
            voter_ip = request.remote_addr

            if session.get('user_id'):
                cursor.execute(
                    "SELECT 1 FROM votes WHERE survey_id = %s AND user_id = %s",
                    (survey_id, session['user_id'])
                )
            else:
                cursor.execute(
                    "SELECT 1 FROM votes WHERE survey_id = %s AND voter_ip = %s",
                    (survey_id, voter_ip)
                )
            user_voted = cursor.fetchone() is not None

        return render_template('survey.html', survey=survey, options=options, is_voted=user_voted)

    # Голосование
    @app.route('/submit_vote', methods=['POST'])
    def submit_vote():
        survey_id = request.form['survey_id']
        option_id = request.form.get('option_id')
        user_id = session.get('user_id')
        voter_ip = request.remote_addr if not user_id else None

        if not option_id:
            flash('Please select an option to vote!')
            return redirect(url_for('get_survey', survey_id=survey_id))

        conn = connect()
        with conn.cursor() as cursor:
            # Проверяем, можно ли голосовать анонимно
            cursor.execute("SELECT is_anonymous FROM surveys WHERE id = %s", (survey_id,))
            survey = cursor.fetchone()

            # Если опрос не анонимный и пользователь не авторизован
            if not survey[0] and not user_id:
                flash('This survey requires registration to vote!')
                return redirect(url_for('login'))

            # Проверяем, голосовал ли уже (по user_id или IP)
            if user_id:
                cursor.execute(
                    "SELECT 1 FROM votes WHERE survey_id = %s AND user_id = %s",
                    (survey_id, user_id)
                )
            else:
                cursor.execute(
                    "SELECT 1 FROM votes WHERE survey_id = %s AND voter_ip = %s",
                    (survey_id, voter_ip)
                )

            if cursor.fetchone():
                flash('You have already voted in this survey!')
                return redirect(url_for('get_survey', survey_id=survey_id))

            # Создаем запись голоса
            cursor.execute(
                "INSERT INTO votes (survey_id, user_id, voter_ip) VALUES (%s, %s, %s) RETURNING id",
                (survey_id, user_id, voter_ip)
            )
            vote_id = cursor.fetchone()[0]

            # Связываем голос с вариантом
            cursor.execute(
                "INSERT INTO vote_options (vote_id, option_id) VALUES (%s, %s)",
                (vote_id, option_id)
            )
            conn.commit()

        flash('Vote submitted successfully!')
        return redirect(url_for('get_survey', survey_id=survey_id))

    # Добавление варианта ответа
    @app.route('/add-option/<int:survey_id>', methods=['GET', 'POST'])
    @login_required
    def add_option(survey_id):
        if request.method == 'POST':
            description = request.form['description']

            conn = connect()
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO options (survey_id, description) VALUES (%s, %s)",
                    (survey_id, description)
                )
                conn.commit()

            flash('Option added successfully!')
            return redirect(url_for('add_option', survey_id=survey_id))

        conn = connect()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, description FROM options WHERE survey_id = %s",
                (survey_id,)
            )
            options = cursor.fetchall()

        return render_template('add_option.html', survey_id=survey_id, options=options)

    # Просмотр результатов
    @app.route('/survey/<int:survey_id>/votes')
    def view_votes(survey_id):
        conn = connect()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.description, COUNT(vo.id) as vote_count
                FROM options o 
                LEFT JOIN vote_options vo ON o.id = vo.option_id 
                WHERE o.survey_id = %s 
                GROUP BY o.id, o.description
                ORDER BY vote_count DESC
            """, (survey_id,))
            votes = cursor.fetchall()

            cursor.execute("SELECT title FROM surveys WHERE id = %s", (survey_id,))
            survey_title = cursor.fetchone()[0]

        return render_template('votes.html', votes=votes, survey_title=survey_title, survey_id=survey_id)

    # Удаление опроса
    @app.route('/delete-survey/<int:survey_id>', methods=['POST'])
    @login_required
    def delete_survey(survey_id):
        conn = connect()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM surveys WHERE id = %s", (survey_id,))
            conn.commit()

        flash('Survey deleted successfully!')
        return redirect(url_for('index'))
