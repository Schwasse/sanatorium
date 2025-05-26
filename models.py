from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    is_admin = db.Column(db.Boolean, default=False)
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Добавьте autoincrement
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    goal = db.Column(db.String(100))
    budget = db.Column(db.Integer)
    region = db.Column(db.String(100))
    sanatorium_type = db.Column(db.String(100))
    services = db.Column(db.String(200))
    priorities = db.Column(db.String(200))
    criteria_weights = db.Column(db.JSON)
    comparison_matrix = db.Column(db.JSON)  # Сохраненная матрица сравнений
    consistency_ratio = db.Column(db.Float)  # Коэффициент согласованности

class Sanatorium(db.Model):
    __tablename__ = 'sanatoriums'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50), nullable=False, default="Россия")
    region = db.Column(db.String(50))  # Для фильтра по регионам
    sanatorium_type = db.Column(db.String(50))  # Тип санатория
    description = db.Column(db.Text)
    price_per_night = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    website = db.Column(db.String(255))
    food_type = db.Column(db.String(100))  # Тип питания
    has_wifi = db.Column(db.Boolean, default=False)
    has_tv = db.Column(db.Boolean, default=False)
    has_ac = db.Column(db.Boolean, default=False)
    has_minibar = db.Column(db.Boolean, default=False)
    has_safe = db.Column(db.Boolean, default=False)
    has_balcony = db.Column(db.Boolean, default=False)
    has_pool = db.Column(db.Boolean, default=False)  # Для фильтра
    has_spa = db.Column(db.Boolean, default=False)  # Для фильтра
    photo_filename = db.Column(db.String(255))  # Сохраняем имя файла
    has_entertainment = db.Column(db.Boolean, default=False)  # Для фильтра
    location_score = db.Column(db.Float)  # Оценка местоположения (1-5)
    comfort_score = db.Column(db.Float)  # Оценка комфорта (1-5)
    service_score = db.Column(db.Float)  # Оценка сервиса (1-5)
    treatment_score = db.Column(db.Float)  # Оценка лечения (1-5)
    food_score = db.Column(db.Float)  # Оценка питания (1-5)
    price_score = db.Column(db.Float)  # Оценка цены (1-5)
    resort = db.Column(db.String(100))  # Название курорта
    specialization = db.Column(db.String(255))  # Например: сердечно-сосудистая система, опорно-двигательная и т.д.
    equipment = db.Column(db.Text)  # Например: аппарат УВЧ, ингаляторы, ванны и т.д.
    room_types = db.Column(db.String(255))  # Например: стандарт, люкс, апартаменты и т.д.
    attractions_distance = db.Column(db.String(255))  # Например: "1.5 км до пляжа, 3 км до музея"
