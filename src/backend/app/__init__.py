from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.routes.upload import upload_bp
    app.register_blueprint(upload_bp)

    from app.routes.requirement_routes import requirement_bp
    app.register_blueprint(requirement_bp)

    return app