from datetime import datetime
from .database import db
import jwt
from flask import current_app
import bcrypt
from datetime import timedelta
import json

class User:
    @staticmethod
    def create(username, email, password):
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) "
                "OUTPUT INSERTED.user_id VALUES (?, ?, ?, ?)",
                (username, email, hashed_pw.decode('utf-8'), salt.decode('utf-8'))
            )
            user_id = cursor.fetchone()[0]
            conn.commit()
            return user_id

    @staticmethod
    def authenticate(username, password):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, password_hash, salt FROM users "
                "WHERE username = ? AND is_active = 1",
                (username, )
            )
            user = cursor.fetchone()
            
        if user:
            user_id, stored_hash, salt = user
            if bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8')).decode('utf-8') == stored_hash:
                return user_id
        return None

    @staticmethod
    def generate_tokens(user_id):
        access_token = jwt.encode({
            'sub': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']),
            'iat': datetime.utcnow(),
            'type': 'access'
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

        refresh_token = jwt.encode({
            'sub': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_REFRESH_TOKEN_EXPIRES']),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

        # Guardar refresh token en la base de datos
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO refresh_tokens (user_id, token, expires_at) "
                "VALUES (?, ?, ?)",
                user_id, refresh_token, 
                datetime.utcnow() + timedelta(seconds=current_app.config['JWT_REFRESH_TOKEN_EXPIRES'])
            )
            conn.commit()

        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

class Movie:
    @staticmethod
    def get_user_history(user_id):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT movie_id, rating FROM user_history "
                "WHERE user_id = ? ORDER BY watched_at DESC",
                user_id
            )
            return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

    @staticmethod
    def add_to_history(user_id, movie_id, rating=None):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "MERGE INTO user_history AS target "
                "USING (VALUES (?, ?, ?)) AS source (user_id, movie_id, rating) "
                "ON target.user_id = source.user_id AND target.movie_id = source.movie_id "
                "WHEN MATCHED THEN "
                "    UPDATE SET rating = source.rating, watched_at = GETDATE() "
                "WHEN NOT MATCHED THEN "
                "    INSERT (user_id, movie_id, rating) VALUES (source.user_id, source.movie_id, source.rating);",
                user_id, movie_id, rating
            )
            conn.commit()

    @staticmethod
    def cache_movie_details(movie_data):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "MERGE INTO cached_movies AS target "
                "USING (VALUES (?, ?, ?, ?, ?, ?, ?)) AS source "
                "(movie_id, title, overview, poster_path, release_date, genres, last_updated) "
                "ON target.movie_id = source.movie_id "
                "WHEN MATCHED THEN "
                "    UPDATE SET title = source.title, overview = source.overview, "
                "    poster_path = source.poster_path, release_date = source.release_date, "
                "    genres = source.genres, last_updated = source.last_updated "
                "WHEN NOT MATCHED THEN "
                "    INSERT (movie_id, title, overview, poster_path, release_date, genres) "
                "    VALUES (source.movie_id, source.title, source.overview, "
                "    source.poster_path, source.release_date, source.genres);",
                movie_data['id'], movie_data['title'], movie_data.get('overview', ''),
                movie_data.get('poster_path', ''), movie_data.get('release_date', ''),
                json.dumps(movie_data.get('genres', [])), datetime.utcnow()
            )
            conn.commit()