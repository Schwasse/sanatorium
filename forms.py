from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    FloatField,
    BooleanField,
    SubmitField,
    SelectField,
    SelectMultipleField,
    IntegerField
)
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Email, Optional, NumberRange
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms import (
    StringField, PasswordField, SubmitField,
    SelectField, IntegerField, SelectMultipleField,
    RadioField, HiddenField
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange
import numpy as np
from fractions import Fraction
from wtforms.validators import Optional
from wtforms import SelectField
class SanatoriumForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    country = StringField('Страна', default="Россия")
    region = StringField('Регион')
    resort = StringField('Курорт', validators=[Optional()])  # ✅ Новое поле
    specialization = StringField('Специализация', validators=[Optional()])  # ✅ Новое поле
    room_types = StringField('Типы номеров', validators=[Optional()])  # ✅ Новое поле
    equipment = TextAreaField('Оборудование', validators=[Optional()])  # ✅ Новое поле
    attractions_distance = StringField('Расстояние до достопримечательностей', validators=[Optional()])  # ✅ Новое поле
    sanatorium_type = StringField('Тип санатория', validators=[Optional()])

    location_score = FloatField('Оценка местоположения', validators=[Optional()])
    comfort_score = FloatField('Оценка комфорта', validators=[Optional()])
    service_score = FloatField('Оценка сервиса', validators=[Optional()])
    treatment_score = FloatField('Оценка лечения', validators=[Optional()])
    food_score = FloatField('Оценка питания', validators=[Optional()])
    price_score = FloatField('Оценка цены', validators=[Optional()])

    description = TextAreaField('Описание')
    price_per_night = FloatField('Цена за ночь', validators=[DataRequired()])
    rating = FloatField('Рейтинг')
    phone = StringField('Телефон')
    email = StringField('Email')
    website = StringField('Вебсайт')
    food_type = StringField('Тип питания')

    has_wifi = BooleanField('Wi-Fi')
    has_tv = BooleanField('Телевизор')
    has_ac = BooleanField('Кондиционер')
    has_minibar = BooleanField('Мини-бар')
    has_safe = BooleanField('Сейф')
    has_balcony = BooleanField('Балкон')
    has_pool = BooleanField('Бассейн')
    has_spa = BooleanField('Спа')
    has_entertainment = BooleanField('Развлечения')

    photo = FileField('Фото санатория', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения!')
    ])

    submit = SubmitField('Сохранить')
class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя',
                           validators=[DataRequired(), Length(min=2, max=150)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Пароль',
                             validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтверждение пароля',
                                     validators=[DataRequired(),
                                                 EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    username = StringField('Имя пользователя',
                           validators=[DataRequired()])
    password = PasswordField('Пароль',
                             validators=[DataRequired()])
    submit = SubmitField('Войти')


class UserProfileForm(FlaskForm):
    goal = SelectField('Цель отдыха',
                       choices=[('отдых', 'Отдых'),
                                ('лечение', 'Лечение'),
                                ('профилактика', 'Профилактика')],
                       validators=[DataRequired()])
    budget = IntegerField('Бюджет',
                          validators=[DataRequired(), NumberRange(min=0)])
    region = StringField('Предпочитаемый регион',
                         validators=[DataRequired()])
    sanatorium_type = SelectField('Тип санатория',
                                  choices=[('профильный', 'Профильный'),
                                           ('многопрофильный', 'Многопрофильный')],
                                  validators=[DataRequired()])
    services = SelectMultipleField('Предпочитаемые услуги',
                                   choices=[
                                       ('бассейн', 'Бассейн'),
                                       ('спа', 'СПА-процедуры'),
                                       ('лечение', 'Лечение'),
                                       ('питание', 'Питание')
                                   ])
    submit = SubmitField('Сохранить профиль')


class AHPCriteriaForm(FlaskForm):
    CRITERIA = {
        'price': {'name': 'Цена', 'description': 'Стоимость проживания', 'icon': 'fa-ruble-sign', 'inverse': True},
        'comfort': {'name': 'Удобства', 'description': 'Уровень комфорта', 'icon': 'fa-couch'},
        'treatment': {'name': 'Лечение', 'description': 'Качество медицинских услуг', 'icon': 'fa-heartbeat'},
        'location': {'name': 'Расположение', 'description': 'Удобство расположения', 'icon': 'fa-map-marker-alt'},
        'service': {'name': 'Услуги', 'description': 'Наличие дополнительных услуг', 'icon': 'fa-concierge-bell'}
    }

    for i, (key1, data1) in enumerate(CRITERIA.items()):
        for key2, data2 in list(CRITERIA.items())[i + 1:]:
            field_name = f"{key1}_vs_{key2}"
            locals()[field_name] = RadioField(
                label=f"Сравнение: {data1['name']} ↔ {data2['name']}",
                description=f"Что для вас важнее: {data1['description']} или {data2['description']}?",
                choices=[
                    ('9', f"{data1['name']} абсолютно важнее"),
                    ('7', f"{data1['name']} значительно важнее"),
                    ('5', f"{data1['name']} существенно важнее"),
                    ('3', f"{data1['name']} немного важнее"),
                    ('1', 'Одинаково важно'),
                    ('1/3', f"{data2['name']} немного важнее"),
                    ('1/5', f"{data2['name']} существенно важнее"),
                    ('1/7', f"{data2['name']} значительно важнее"),
                    ('1/9', f"{data2['name']} абсолютно важнее"),
                ],
                validators=[DataRequired()],
                render_kw={'data-criterion1': key1, 'data-criterion2': key2, 'class': 'comparison-field'}
            )

    comparison_matrix = HiddenField()
    weights_json = HiddenField()
    consistency_ratio = HiddenField()
    submit = SubmitField('Рассчитать приоритеты', render_kw={'class': 'btn btn-primary btn-lg'})

    def build_comparison_matrix(self):
        n = len(self.CRITERIA)
        criteria = list(self.CRITERIA.keys())
        matrix = np.ones((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                field_name = f"{criteria[i]}_vs_{criteria[j]}"
                field = getattr(self, field_name)
                value = float(Fraction(field.data))
                matrix[i, j] = value
                matrix[j, i] = 1 / value

        return matrix

    def calculate_weights(self):
        matrix = self.build_comparison_matrix()
        n = matrix.shape[0]

        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        max_idx = np.argmax(np.real(eigenvalues))
        weights = np.real(eigenvectors[:, max_idx])
        weights = np.abs(weights) / np.sum(np.abs(weights))

        lambda_max = np.max(np.real(eigenvalues))
        ci = (lambda_max - n) / (n - 1)
        ri = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12}.get(n, 1.24)
        cr = ci / ri if ri != 0 else 0

        import json
        self.comparison_matrix.data = json.dumps(matrix.tolist())
        self.weights_json.data = json.dumps({k: float(v) for k, v in zip(self.CRITERIA.keys(), weights)})
        self.consistency_ratio.data = str(cr)

        return weights, cr

