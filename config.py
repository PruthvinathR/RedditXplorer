# import os

# import sys
# import os

# # Get the absolute path of the project root directory
# project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# # Add the project root to the Python path if it's not already there
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

# class Config:
#     SECRET_KEY = os.getenv('SECRET_KEY', 'mysecret')
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///app.db')
#     SQLALCHEMY_TRACK_MODIFICATIONS = False

# class DevelopmentConfig(Config):
#     DEBUG = True
#     ENV = 'development'

# class ProductionConfig(Config):
#     DEBUG = False
#     ENV = 'production'