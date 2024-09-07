from flask import Flask
from app.reddit_app import reddit_bp
from app.reddit_app.controllers.PostController import post_controller_bp

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(reddit_bp)
    app.register_blueprint(post_controller_bp)

    return app
