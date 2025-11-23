# Все маршруты приложения - с использованием логических классов
from flask import render_template, request, redirect, url_for, flash, session
import functools
from app.db.survey_logic import LogicProvider as SurveyLogic
from app.db.user_logic import LogicProvider as UserLogic
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

    # Инициализация логических провайдеров
    survey_logic = SurveyLogic(provider='raw')
    user_logic = UserLogic(provider='raw')

    # Главная страница - список опросов
    @app.route("/")
    def index():
        # Используем логический класс для получения опросов
        surveys = survey_logic.get_all_surveys()
        return render_template('surveys.html', all_surveys=surveys)

    # Регистрация
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            user_name = request.form['user_name']
            password = request.form['password']

            try:
                # Используем логический класс для создания пользователя
                user_logic.create_user(user_name=user_name, password=password)
                flash('Registration successful! Please login with your credentials.')
                return redirect(url_for('login'))

            except Exception as e:
                flash(f'Registration error: {e}')

        return render_template('registration.html')

    # Вход
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user_name = request.form['user_name']
            password = request.form['password']

            # Используем логический класс для получения пользователя
            user = user_logic.get_user(user_name)

            if user and user['password'] == password:
                session['user_id'] = user['id']
                session['user_name'] = user['user_name']
                session['loggedin'] = True
                return redirect(url_for('index'))
            else:
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

            # Используем логический класс для создания опроса
            result = survey_logic.create_survey(
                title=title,
                description=description,
                created_by=created_by,
                is_anonymous=is_anonymous
            )
            survey_id = result['id']

            flash('Survey created successfully! Add options')
            return redirect(url_for('add_option', survey_id=survey_id))

        return render_template('create_survey.html')

    # Просмотр опроса
    @app.route('/survey/<int:survey_id>')
    def get_survey(survey_id):
        # Используем логические классы для получения данных
        survey = survey_logic.get_survey(survey_id)
        options = survey_logic.get_survey_options(survey_id)

        # Проверяем, голосовал ли пользователь
        user_voted = False
        voter_ip = request.remote_addr

        # Для проверки голосования используем прямое подключение
        conn = connect()
        with conn.cursor() as cursor:
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

        # Используем прямое подключение для сложной логики голосования
        conn = connect()
        with conn.cursor() as cursor:
            # Проверяем, можно ли голосовать анонимно
            cursor.execute("SELECT is_anonymous FROM surveys WHERE id = %s", (survey_id,))
            survey = cursor.fetchone()

            # Если опрос не анонимный и пользователь не авторизован
            if not survey[0] and not user_id:
                flash('This survey requires registration to vote!')
                return redirect(url_for('login'))

            # Проверяем, голосовал ли уже
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

            # Используем логический класс для добавления варианта
            survey_logic.add_option(survey_id, description)
            flash('Option added successfully!')
            return redirect(url_for('add_option', survey_id=survey_id))

        # Используем логический класс для получения вариантов
        options = survey_logic.get_survey_options(survey_id)
        return render_template('add_option.html', survey_id=survey_id, options=options)

    # Просмотр результатов
    @app.route('/survey/<int:survey_id>/votes')
    def view_votes(survey_id):
        # Для сложных запросов используем прямое подключение
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
        # Используем логический класс для удаления опроса
        survey_logic.delete_survey(survey_id)
        flash('Survey deleted successfully!')
        return redirect(url_for('index'))
