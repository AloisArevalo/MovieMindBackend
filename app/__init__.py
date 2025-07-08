from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from .database import db
from .recommendation_engine import RecommendationEngine
from .auth import auth_blueprint, jwt
from .recommendations import recommendations_blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # Inicializar extensiones
    CORS(app)
    db.init_app(app)
    
    # Configurar JWT
    #from .auth import auth_blueprint
    jwt.init_app(app)

    recommendation_engine = RecommendationEngine(app)
    
    # Registrar blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(recommendations_blueprint, url_prefix='/api')

    @app.route('/')
    def home():
        return jsonify({
            "message": "Bienvenido a MovieMind API",
            "endpoints": {
                "auth": "/auth",
                "recommendations": "/api/recommend"
            }
        })
    
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    return app