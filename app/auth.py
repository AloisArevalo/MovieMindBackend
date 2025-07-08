from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, 
    create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .database import db
import datetime

# Crear el Blueprint de autenticación
auth_blueprint = Blueprint('auth', __name__)

# Configuración de JWT (se inicializa en create_app)
jwt = JWTManager()

@auth_blueprint.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validación básica
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'error': 'Faltan campos obligatorios'}), 400
    
    # Verificar si el usuario ya existe
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", 
                      (data['username'], data['email']))
        if cursor.fetchone():
            return jsonify({'error': 'El usuario o email ya existe'}), 400
    
    # Crear nuevo usuario
    try:
        user_id = User.create(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        
        # Generar tokens
        access_token = create_access_token(identity=user_id)
        refresh_token = create_refresh_token(identity=user_id)
        
        return jsonify({
            'message': 'Usuario registrado exitosamente',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_blueprint.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Faltan campos obligatorios'}), 400
    
    # Autenticar usuario
    user_id = User.authenticate(data['username'], data['password'])
    if not user_id:
        return jsonify({'error': 'Credenciales inválidas'}), 401
    
    # Generar tokens
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)
    
    return jsonify({
        'message': 'Inicio de sesión exitoso',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user_id': user_id
    })

@auth_blueprint.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({'access_token': new_token})

@auth_blueprint.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({'user_id': current_user}), 200

@auth_blueprint.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']
    
    # Implementar lista negra de tokens si es necesario
    # (requiere configuración adicional en JWT)
    
    return jsonify({'message': 'Sesión cerrada exitosamente'}), 200

# Callback para verificar tokens en la lista negra
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    # Implementar lógica para verificar tokens revocados
    # (requiere tabla en la base de datos)
    return False