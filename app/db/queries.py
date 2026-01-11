GET_ALL_SURVEYS = """
SELECT id, title, description, created_by, created_at, is_anonymous
FROM surveys
ORDER BY created_at DESC;
"""

GET_SURVEY = """
SELECT s.id, s.title, s.description, s.created_by, s.created_at, s.is_anonymous, u.user_name
FROM surveys s
LEFT JOIN users u ON s.created_by = u.id
WHERE s.id = %s;
"""

GET_OPTIONS_FOR_SURVEY = """
SELECT id, description
FROM options
WHERE survey_id = %s;
"""

CREATE_SURVEY = """
INSERT INTO surveys (title, description, created_by, is_anonymous)
VALUES (%s, %s, %s, %s)
RETURNING id;
"""

CREATE_OPTION = """
INSERT INTO options (survey_id, description)
VALUES (%s, %s)
RETURNING id;
"""

CREATE_USER = """
INSERT INTO users (user_name, password)
VALUES (%s, %s)
RETURNING id;
"""

GET_USER_BY_USERNAME = """
SELECT id, user_name, password
FROM users
WHERE user_name = %s;
"""
