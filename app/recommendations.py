from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .recommendation_engine import RecommendationEngine
from .tmdb_service import TMDBService
from .models import Movie
from .database import db

# Crear el Blueprint de recomendaciones
recommendations_blueprint = Blueprint('recommendations', __name__)

@recommendations_blueprint.route('/recommend', methods=['GET'])
@jwt_required()
def get_recommendations():
    user_id = get_jwt_identity()
    
    # Crea una instancia al iniciar
    engine = RecommendationEngine()

    try:
        # Obtener recomendaciones
        recommendations = engine.get_recommendations(user_id)
        
        # Formatear respuesta
        result = []
        for movie in recommendations:
            result.append({
                'movie_id': movie['id'],
                'title': movie['title'],
                'overview': movie['overview'],
                'poster_path': movie['poster_path'],
                'release_date': movie['release_date']
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recommendations_blueprint.route('/rate', methods=['POST'])
@jwt_required()
def rate_movie():
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'movie_id' not in data or 'rating' not in data:
        return jsonify({'error': 'Se requieren movie_id y rating'}), 400
    
    try:
        Movie.add_to_history(user_id, data['movie_id'], data['rating'])
        return jsonify({'message': 'Valoración guardada exitosamente'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@recommendations_blueprint.route('/search', methods=['GET'])
def search_movies():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Parámetro de búsqueda "q" requerido'}), 400
    
    try:
        results = TMDBService.search_movies(query)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500