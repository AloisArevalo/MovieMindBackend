from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import Movie
from .tmdb_service import TMDBService
import pandas as pd
import joblib
import os
from .database import db
from flask import current_app
import logging

class RecommendationEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.tfidf = TfidfVectorizer(stop_words='english')
            self.cosine_sim = None
            self.movie_features = None
            self._initialized = True
            self.app = None
        print(f"Instancia creada (ID: {id(self)})")

    def init_app(self, app):
        self.app = app
        with app.app_context():
            try:
                print("Inicializando motor de recomendaciones...")
                self.train_model()  # <-- Debe ejecutarse aquí
                if self.cosine_sim is None:
                    raise RuntimeError("Falló el entrenamiento de la matriz")
                print(f"Matriz entrenada. Dimensiones: {self.cosine_sim.shape}")
            except Exception as e:
                print(f"Error catastrófico en train_model(): {str(e)}")
                raise

    def load_or_train_model(self):
        cache_file = os.path.join(self.app.instance_path, 'recommendation_model.joblib')
        
        if os.path.exists(cache_file):
            self.tfidf, self.cosine_sim, self.movie_features = joblib.load(cache_file)
        else:
            self.train_model()
            os.makedirs(self.app.instance_path, exist_ok=True)
            joblib.dump((self.tfidf, self.cosine_sim, self.movie_features), cache_file)

    def train_model(self):
        """Entrena la matriz de similitud"""
        print("Iniciando entrenamiento del modelo...")
        
        # 1. Verificar conexión a la base de datos
        try:
            test_conn = db.get_raw_connection_test()
            test_conn.close()
        except Exception as e:
            print(f"❌ Error de conexión a la base de datos: {str(e)}")
            return False

        # 2. Obtener y validar datos
        movies = self._get_popular_movies_for_training()
        if not movies:
            print("""
            ❌ No se pudieron obtener películas de la base de datos.
            Posibles causas:
            1. La tabla 'user_history' está vacía
            2. Problemas de permisos de lectura
            3. Error en la conexión a la base de datos
            
            Verifica con:
            SELECT * FROM user_history;
            """)
            return False

        print(f"📊 Películas encontradas: {len(movies)}")
        return True

        # 3. Procesar características
        features = []
        valid_movies = []
        for movie in movies:
            details = TMDBService.get_movie_details(movie['movie_id'])
            if details:
                features.append(self._create_feature_string(details))
                valid_movies.append(movie['movie_id'])

        if len(valid_movies) < 3:
            print(f"❌ Solo {len(valid_movies)} películas válidas. Se necesitan al menos 3.")
            return False

        # 4. Entrenamiento final
        try:
            tfidf_matrix = self.tfidf.fit_transform(features)
            self.cosine_sim = cosine_similarity(tfidf_matrix)
            print(f"✅ Entrenado con {len(valid_movies)} películas. Matriz: {self.cosine_sim.shape}")
            return True
        except Exception as e:
            print(f"❌ Error en entrenamiento: {str(e)}")
            return False

    def _get_popular_movies_for_training(self):
        """Versión final probada"""
        try:
            with self.app.app_context():
                with db.get_connection() as conn:  # Usa el context manager corregido
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT movie_id 
                        FROM user_history
                        GROUP BY movie_id
                        ORDER BY COUNT(*) DESC
                    """)
                    return [{'movie_id': row[0]} for row in cursor.fetchall()]
        except Exception as e:
            self.app.logger.error(f"Error SQL definitivo: {str(e)}")
            return []

    def _create_feature_string(self, movie_details):
        """Combina características para el modelo"""
        genres = ' '.join([genre['name'] for genre in movie_details.get('genres', [])])
        overview = movie_details.get('overview', '')[:500]  # Limita tamaño
        return f"{genres} {overview}"

    def get_recommendations(self, user_id, num_recommendations=5):

        if self.cosine_sim is None:
            print("Advertencia: La matriz de similitud no está entrenada")
            return []

        for rating in user_history:
            movie_data = TMDBService.get_movie_details(rating['movie_id'])

            if not movie_data:
                print(f"¡ATENCIÓN! movie_id {rating['movie_id']} no existe en TMDB")

        if not user_history:
            print(f"Usuario {user_id} no tiene historial")
            return []
        
        print(f"Buscando recomendaciones para usuario {user_id}...")
        user_history = Movie.get_user_history(user_id)
        print("Historial del usuario:", user_history)
        
        # Obtener la mejor valorada del usuario
        best_rated = max(user_history, key=lambda x: x['rating'])
        
        try:
            idx = self.movie_features[self.movie_features == best_rated['movie_id']].index[0]
            sim_scores = list(enumerate(self.cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            
            # Excluir películas ya vistas
            watched_movies = [m['movie_id'] for m in user_history]
            sim_indices = [
                i for i, _ in sim_scores[1:num_recommendations*2+1] 
                if self.movie_features.iloc[i] not in watched_movies
            ][:num_recommendations]
            
            return [TMDBService.get_movie_details(self.movie_features.iloc[i]) for i in sim_indices]
        except:
            return []

recommendation_engine = RecommendationEngine()