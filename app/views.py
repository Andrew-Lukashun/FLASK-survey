from flask import render_template, request, redirect, url_for, flash, session
import functools
from app.db.survey_logic import LogicProvider as SurveyLogic
from app.db.user_logic import LogicProvider as UserLogic

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

    survey_logic = SurveyLogic(provider='raw')
    user_logic = UserLogic(provider='raw')

    @app.route("/")
    def index():
        surveys = survey_logic.get_all_surveys()
        return render_template('surveys.html', all_surveys=surveys)

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            user_name = request.form['user_name']
            password = request.form['password']
            try:
                user_logic.create_user(user_name=user_name, password=password)
                flash('Registration successful! Now you can login.')
                return redirect(url_for('login'))
            except Exception as e:
                if 'unique constraint' in str(e).lower():
                    flash('This username is already taken. Please choose another one.')
                else:
                    flash(f'Registration error: {e}')
        return render_template('registration.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user_name = request.form['user_name']
            password = request.form['password']

            user = user_logic.get_user(user_name)

            if user and user.get('password') == password:
                session['loggedin'] = True
                session['user_id'] = user['id']
                session['user_name'] = user['user_name']
                flash('Logged in successfully!')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/create-survey', methods=['GET', 'POST'])
    @login_required
    def create_survey():
        if request.method == 'POST':
            result = survey_logic.create_survey(
                title=request.form['title'],
                description=request.form['description'],
                created_by=session.get('user_id'),
                is_anonymous=request.form.get('is_anonymous') == 'true'
            )
            return redirect(url_for('add_option', survey_id=result['id']))
        return render_template('create_survey.html')

    @app.route('/survey/<int:survey_id>')
    def get_survey(survey_id):
        survey = survey_logic.get_survey(survey_id)
        if not survey:
            return "Survey not found", 404

        options = survey_logic.get_survey_options(survey_id)

        #  может ли пользователь голосовать
        user_id = session.get('user_id')
        is_loggedin = session.get('loggedin')

        # Проверяем, проголосовал ли уже этот человек
        is_voted = survey_logic.check_vote(survey_id, user_id, request.remote_addr)

        # Определяем, разрешено ли голосование
        can_vote = survey['is_anonymous'] or is_loggedin

        return render_template(
            'survey.html',
            survey=survey,
            options=options,
            is_voted=is_voted,
            can_vote=can_vote
        )

    @app.route('/submit-vote', methods=['POST'])
    def submit_vote():
        survey_id = request.form.get('survey_id')
        option_id = request.form.get('option_id')

        survey_logic.submit_vote(
            survey_id=survey_id,
            option_id=option_id,
            user_id=session.get('user_id'),
            voter_ip=request.remote_addr
        )
        flash('Vote submitted!')
        return redirect(url_for('view_votes', survey_id=survey_id))

    @app.route('/add-option/<int:survey_id>', methods=['GET', 'POST'])
    @login_required
    def add_option(survey_id):
        if request.method == 'POST':
            survey_logic.add_option(survey_id, request.form['description'])
            return redirect(url_for('add_option', survey_id=survey_id))
        options = survey_logic.get_survey_options(survey_id)
        return render_template('add_option.html', survey_id=survey_id, options=options)

    @app.route('/survey/<int:survey_id>/votes')
    def view_votes(survey_id):
        votes = survey_logic.get_survey_results(survey_id)
        survey_title = survey_logic.get_survey_title(survey_id)

        return render_template(
            'votes.html',
            votes=votes,
            survey_title=survey_title,
            survey_id=survey_id
        )

    @app.route('/delete-survey/<int:survey_id>', methods=['POST'])
    @login_required
    def delete_survey(survey_id):
        survey_logic.delete_survey(survey_id)
        flash('Survey deleted')
        return redirect(url_for('index'))
