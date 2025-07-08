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
    def get_connection():
        """Versión corregida que funciona con contexto Flask"""
        if not current_app:
            raise RuntimeError("No se encontró la aplicación Flask")
        
        conn_str = f"""
            DRIVER={{{current_app.config.get('SQL_DRIVER', 'ODBC Driver 17 for SQL Server')}}};
            SERVER={current_app.config['SQL_SERVER']};
            DATABASE={current_app.config['SQL_DATABASE']};
            UID={current_app.config['SQL_USERNAME']};
            PWD={current_app.config['SQL_PASSWORD']}
        """
        conn = None
        try:
            conn = pyodbc.connect(conn_str)
            yield conn
        finally:
            if conn:
                conn.close()

    def get_raw_connection_test():
        """Método solo para pruebas de conexión"""
        conn_str = f"""
            DRIVER={{{current_app.config.get('SQL_DRIVER', 'ODBC Driver 17 for SQL Server')}}};
            SERVER={current_app.config['SQL_SERVER']};
            DATABASE={current_app.config['SQL_DATABASE']};
            UID={current_app.config['SQL_USERNAME']};
            PWD={current_app.config['SQL_PASSWORD']}
        """
        return pyodbc.connect(conn_str)

    def teardown(self, exception):
        pass

db = SQLServer()