# CLI команды для управления базой данных
import click
from app.db.raw_connection import connect

@click.command('init-db')
def init_db_command():
    conn = connect()
    with conn.cursor() as cursor:
        with open('app/db/schema.sql', 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        conn.commit()
    click.echo('Database initialized successfully!')

def initialize_commands(app):
    app.cli.add_command(init_db_command)