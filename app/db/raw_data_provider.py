from app.db.raw_connection import connect
from psycopg2.extras import RealDictCursor

class RawDataProvider:
    @staticmethod
    def create_survey(**kwargs):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "INSERT INTO surveys (title, description, created_by, is_anonymous) VALUES (%s, %s, %s, %s) RETURNING id",
                (kwargs['title'], kwargs['description'], kwargs['created_by'], kwargs['is_anonymous'])
            )
            survey_id = cursor.fetchone()['id']
            conn.commit()
            return {'id': survey_id}

    @staticmethod
    def get_all_surveys():
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT s.id, s.title, s.description, s.created_by, s.created_at, s.is_anonymous, u.user_name 
                FROM surveys s 
                LEFT JOIN users u ON s.created_by = u.id 
                ORDER BY s.created_at DESC
            """)
            return cursor.fetchall()

    @staticmethod
    def get_survey(survey_id):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT s.id, s.title, s.description, s.created_by, s.created_at, s.is_anonymous, u.user_name
                FROM surveys s
                LEFT JOIN users u ON s.created_by = u.id
                WHERE s.id = %s
            """, (survey_id,))
            return cursor.fetchone()

    @staticmethod
    def get_user(user_name):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, user_name, password FROM users WHERE user_name = %s", (user_name,))
            return cursor.fetchone()

    @staticmethod
    def create_user(**kwargs):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "INSERT INTO users (user_name, password) VALUES (%s, %s) RETURNING id",
                (kwargs['user_name'], kwargs['password'])
            )
            user_id = cursor.fetchone()['id']
            conn.commit()
            return {'id': user_id}

    @staticmethod
    def get_survey_options(survey_id):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, description FROM options WHERE survey_id = %s", (survey_id,))
            return cursor.fetchall()

    @staticmethod
    def add_option(survey_id, description):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("INSERT INTO options (survey_id, description) VALUES (%s, %s)", (survey_id, description))
            conn.commit()

    @staticmethod
    def delete_survey(survey_id):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("DELETE FROM surveys WHERE id = %s", (survey_id,))
            conn.commit()

    @staticmethod
    def check_vote(survey_id, user_id=None, voter_ip=None):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if user_id:
                cursor.execute("SELECT 1 FROM votes WHERE survey_id = %s AND user_id = %s", (survey_id, user_id))
            else:
                cursor.execute("SELECT 1 FROM votes WHERE survey_id = %s AND voter_ip = %s", (survey_id, voter_ip))
            return cursor.fetchone() is not None

    @staticmethod
    def submit_vote(survey_id, option_id, user_id=None, voter_ip=None):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "INSERT INTO votes (survey_id, user_id, voter_ip) VALUES (%s, %s, %s) RETURNING id",
                (survey_id, user_id, voter_ip)
            )
            vote_id = cursor.fetchone()['id']
            cursor.execute("INSERT INTO vote_options (vote_id, option_id) VALUES (%s, %s)", (vote_id, option_id))
            conn.commit()

    @staticmethod
    def get_survey_results(survey_id):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT o.description, COUNT(vo.id) as vote_count
                FROM options o 
                LEFT JOIN vote_options vo ON o.id = vo.option_id 
                WHERE o.survey_id = %s 
                GROUP BY o.id, o.description
                ORDER BY vote_count DESC
            """, (survey_id,))
            return cursor.fetchall()

    @staticmethod
    def get_survey_title(survey_id):
        conn = connect()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT title FROM surveys WHERE id = %s", (survey_id,))
            res = cursor.fetchone()
            return res['title'] if res else None
