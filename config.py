import os
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
class Config:
    SECRET_KEY = 'секретный_ключ'  
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Rotshield7@localhost:5433/sanatory'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_CONFIG = {
        'version': 1,
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': 'app.log',
                'formatter': 'detailed'
            },
        },
        'formatters': {
            'detailed': {
                'format': '%(asctime)s %(levelname)s %(message)s'
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['file']
        }
    }
