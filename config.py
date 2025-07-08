from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración de SQL Server
    SQL_SERVER = os.getenv('SQL_SERVER')
    SQL_DATABASE = os.getenv('SQL_DATABASE')
    SQL_USERNAME = os.getenv('SQL_USERNAME')
    SQL_PASSWORD = os.getenv('SQL_PASSWORD')
    SQL_DRIVER = os.getenv('SQL_DRIVER')
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Configuración de TMDB
    TMDB_API_KEY = os.getenv('TMDB_API_KEY')
    TMDB_BASE_URL = 'https://api.themoviedb.org/3'
    
    # Configuración de la aplicación
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')