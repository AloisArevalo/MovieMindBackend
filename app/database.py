import pyodbc
from flask import current_app
from contextlib import contextmanager

class SQLServer:
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        app.teardown_appcontext(self.teardown)

    @contextmanager
    def get_connection(self):
        conn_str = (
            f"DRIVER={current_app.config['SQL_DRIVER']};"
            f"SERVER={current_app.config['SQL_SERVER']};"
            f"DATABASE={current_app.config['SQL_DATABASE']};"
            f"UID={current_app.config['SQL_USERNAME']};"
            f"PWD={current_app.config['SQL_PASSWORD']}"
        )
        conn = None
        try:
            conn = pyodbc.connect(conn_str)
            yield conn
        except pyodbc.Error as e:
            current_app.logger.error(f"Database connection failed: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def teardown(self, exception):
        pass

db = SQLServer()