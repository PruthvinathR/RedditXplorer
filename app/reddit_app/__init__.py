
from flask import Blueprint
from app.reddit_app.controllers.post_controller import post_controller_bp

reddit_bp = Blueprint('reddit_blueprint', __name__)

@reddit_bp.route('/')
def index():
    return 'reddit blueprint'
