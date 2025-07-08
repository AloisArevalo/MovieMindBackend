import requests
import json
from flask import current_app
from .models import Movie
from .database import db

class TMDBService:
    @staticmethod
    def get_movie_details(movie_id):
        print(f"Buscando movie_id {movie_id} en TMDB...")
        url = f"{current_app.config['TMDB_BASE_URL']}/movie/{movie_id}"
        params = {
            'api_key': current_app.config['TMDB_API_KEY'],
            'append_to_response': 'credits'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            movie_data = response.json()
            
            # Almacenar en caché
            Movie.cache_movie_details(movie_data)
            
            return movie_data
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"TMDB API error: {e}")
            # Intentar obtener de caché si falla la API
            return TMDBService.get_cached_movie(movie_id)

    @staticmethod
    def get_cached_movie(movie_id):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT movie_id, title, overview, poster_path, release_date, genres "
                "FROM cached_movies WHERE movie_id = ?",
                movie_id
            )
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'overview': row[2],
                    'poster_path': row[3],
                    'release_date': row[4],
                    'genres': json.loads(row[5])
                }
        return None

    @staticmethod
    def search_movies(query):
        url = f"{current_app.config['TMDB_BASE_URL']}/search/movie"
        params = {
            'api_key': current_app.config['TMDB_API_KEY'],
            'query': query,
            'language': 'es-ES'  # Opcional: español
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"TMDB search error: {e}")
            return []