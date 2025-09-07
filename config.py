import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DATABASE = 'database/auth.db'
    RECOMMENDATION_MODEL = 'data/model.pkl'
    DATA_FILE = 'data/input_data.csv'