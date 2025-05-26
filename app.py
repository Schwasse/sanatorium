from flask import Flask, render_template, redirect, url_for, flash, jsonify, abort
from config import Config
from models import db, bcrypt, User, UserProfile, Sanatorium
from forms import RegistrationForm, LoginForm, UserProfileForm, SanatoriumForm
from sqlalchemy.exc import IntegrityError
from flask import session
from forms import AHPCriteriaForm
from ahp import calculate_ahp_weights
from flask import request
from config import UPLOAD_FOLDER
from flask import current_app
from PIL import Image
from evaluation import evaluate_sanatoriums, auto_score_sanatoriums  

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Проверяем, есть ли уже такой username или email
        existing_user = User.query.filter(
            (User.username == form.username.data) |
            (User.email == form.email.data)
        ).first()
        if existing_user:
            flash('Пользователь с таким именем или email уже существует.', 'danger')
            return render_template('register.html', form=form)

        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Вы успешно зарегистрированы!', 'success')
            return redirect(url_for('entrance'))
        except IntegrityError:
            db.session.rollback()
            flash('Ошибка при регистрации. Попробуйте ещё раз.', 'danger')

    return render_template('register.html', form=form)


@app.route('/')
def index():
    # Получаем параметры фильтрации
    sort = request.args.get('sort', '')
    region = request.args.get('region', '')
    sanatorium_type = request.args.get('type', '')
    has_pool = request.args.get('pool', False)
    has_spa = request.args.get('spa', False)
    has_entertainment = request.args.get('entertainment', False)

    # Строим запрос с фильтрами
    query = Sanatorium.query

    if region:
        query = query.filter_by(region=region)
    if sanatorium_type:
        query = query.filter_by(sanatorium_type=sanatorium_type)
    if has_pool:
        query = query.filter_by(has_pool=True)
    if has_spa:
        query = query.filter_by(has_spa=True)
    if has_entertainment:
        query = query.filter_by(has_entertainment=True)

    # Сортировка
    if sort == 'asc':
        query = query.order_by(Sanatorium.price_per_night.asc())
    elif sort == 'desc':
        query = query.order_by(Sanatorium.price_per_night.desc())

    sanatoriums = query.all()

    # Получаем уникальные регионы и типы для фильтров
    regions = db.session.query(Sanatorium.region).distinct().all()
    types = db.session.query(Sanatorium.sanatorium_type).distinct().all()

    return render_template(
        'index.html',
        sanatoriums=sanatoriums,
        regions=[r[0] for r in regions if r[0]],
        types=[t[0] for t in types if t[0]]
    )


@app.route("/podbor")
def podbor():
    return render_template('podbor.html')


@app.route('/entrance', methods=['GET', 'POST'])
def entrance():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin  # Устанавливаем is_admin в соответствии с данными пользователя
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    return render_template('entrance.html', form=form)


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # удаляем пользователя из сессии
    return redirect(url_for('index'))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    # Проверка авторизации с подробным логированием
    if 'user_id' not in session:
        flash("Для доступа к профилю войдите в систему", "warning")
        return redirect(url_for('entrance'))

    try:
        user_id = session['user_id']

        # Получаем или создаем профиль
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        form = UserProfileForm(obj=profile)

        # Обработка POST-запроса
        if form.validate_on_submit():

            if not profile:
                profile = UserProfile(user_id=user_id)

            try:
                # Обновляем данные профиля
                form.populate_obj(profile)

                # Безопасное сохранение services
                services = form.services.data
                if isinstance(services, list):
                    profile.services = ','.join(services)
                else:
                    profile.services = ''

                profile.priorities = ''
                # Сохраняем в БД
                db.session.add(profile)
                db.session.commit()

                flash("Профиль успешно обновлен", "success")
                return redirect(url_for('profile'))  # Редирект на эту же страницу

            except Exception as e:
                db.session.rollback()

                flash("Ошибка при сохранении профиля", "danger")

        # Подготовка данных для формы (GET или невалидный POST)
        if profile and profile.services:
            form.services.data = profile.services.split(',')

        return render_template("profile.html", form=form, profile=profile or {})



    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        flash("Произошла внутренняя ошибка", "danger")
        return redirect(url_for('index'))


@app.route('/ahp', methods=['GET', 'POST'])
def ahp_priorities():
    if 'user_id' not in session:
        flash('Для доступа необходимо войти в систему', 'warning')
        return redirect(url_for('entrance'))

    form = AHPCriteriaForm()
    if form.validate_on_submit():
        try:
            # Рассчитываем веса и коэффициент согласованности
            weights, cr = form.calculate_weights()

            # Проверяем согласованность
            if cr >= 0.1:
                flash(f'Оценки недостаточно согласованны (CR={cr:.2f}). Пожалуйста, пересмотрите сравнения.', 'danger')
                return render_template('ahp.html', form=form)

            # Получаем или создаем профиль
            profile = UserProfile.query.filter_by(user_id=session['user_id']).first()
            if not profile:
                profile = UserProfile(user_id=session['user_id'])
                db.session.add(profile)

            # Преобразуем веса в сериализуемый формат
            criteria_names = ['price', 'comfort', 'treatment', 'location', 'service']


            # Обработка разных форматов весов (numpy array или list)
            if hasattr(weights, 'tolist'):  # Для numpy array
                weights = weights.tolist()

            # Создаем словарь весов
            weights_dict = {
                name: float(weight)
                for name, weight in zip(criteria_names, weights)
            }

            # Сохраняем данные
            profile.criteria_weights = weights_dict
            profile.consistency_ratio = float(cr)

            # Явный коммит с обработкой ошибок
            db.session.commit()

            # Логирование успешного сохранения
            current_app.logger.info(
                f"Сохранены веса для user_id {session['user_id']}: {weights_dict}"
            )

            flash('Приоритеты успешно сохранены!', 'success')
            return redirect(url_for('profile'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(
                f"Ошибка сохранения приоритетов для user_id {session['user_id']}: {str(e)}",
                exc_info=True
            )
            flash('Ошибка при сохранении приоритетов. Пожалуйста, попробуйте еще раз.', 'danger')
            return render_template('ahp.html', form=form)

    return render_template('ahp.html', form=form)


@app.route('/recommend')
def recommend_sanatoriums():
    if 'user_id' not in session:
        flash('Для доступа необходимо войти в систему', 'warning')
        return redirect(url_for('entrance'))

    try:
        current_app.logger.info(f"Начало формирования рекомендаций для user_id: {session['user_id']}")

        # Проверка и генерация оценок санаториев
        if Sanatorium.query.filter(Sanatorium.location_score == None).first():
            current_app.logger.info("Генерация автоматических оценок для санаториев")
            auto_score_sanatoriums()

        # Получаем профиль для диагностики
        profile = UserProfile.query.filter_by(user_id=session['user_id']).first()

        if not profile:
            current_app.logger.error("Профиль пользователя не найден")
            flash('Профиль не найден. Пожалуйста, заполните профиль.', 'warning')
            return redirect(url_for('profile'))

        current_app.logger.info(f"Найден профиль: {profile.id}, критерии: {profile.criteria_weights}")

        # Проверка критериев
        if not profile.criteria_weights:
            current_app.logger.error("criteria_weights отсутствуют или пустые")
            flash('Сначала задайте приоритеты в разделе МАИ', 'warning')
            return redirect(url_for('ahp_priorities'))

        # Формирование рекомендаций
        recommendations = evaluate_sanatoriums(session['user_id'])

        if not recommendations:
            current_app.logger.error("Рекомендации не сформированы, но критерии есть")
            flash('Не удалось сформировать рекомендации. Попробуйте изменить критерии.', 'warning')
            return redirect(url_for('ahp_priorities'))

        current_app.logger.info(f"Успешно сформировано {len(recommendations)} рекомендаций")
        return render_template('recommendations.html', recommendations=recommendations)

    except Exception as e:
        current_app.logger.error(f"Ошибка формирования рекомендаций: {str(e)}", exc_info=True)
        flash('Произошла ошибка при формировании рекомендаций', 'danger')
        return redirect(url_for('index'))

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data and data.get('password') == '1234':  # В реальном приложении используйте хеширование и проверку из БД
        session['user_id'] = 'admin'  # Или реальный ID пользователя
        session['is_admin'] = True  # Явно устанавливаем флаг администратора
        return jsonify({'success': True, 'redirect': url_for('index')})
    return jsonify({'success': False}), 401


import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Убедимся, что папка существует

from PIL import Image
from werkzeug.utils import secure_filename
import os


@app.route('/add_sanatorium', methods=['GET', 'POST'])
def add_sanatorium():
    form = SanatoriumForm()
    if not session.get('is_admin'):
        abort(403)

    if form.validate_on_submit():
        filename = None  # по умолчанию

        if form.photo.data:
            photo_file = form.photo.data
            filename = secure_filename(photo_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                # Открываем и сжимаем изображение
                image = Image.open(photo_file)
                image = image.convert('RGB')
                image.thumbnail((800, 600))  # Максимальные размеры
                image.save(file_path, format='JPEG', quality=85)
            except Exception as e:
                flash(f'Ошибка при обработке изображения: {str(e)}', 'danger')
                return render_template('add_sanatorium.html', form=form)

        try:
            sanatorium = Sanatorium(
                name=form.name.data,
                country=form.country.data,
                region=form.region.data,
                sanatorium_type=form.sanatorium_type.data,
                description=form.description.data,
                price_per_night=form.price_per_night.data,
                rating=form.rating.data,
                phone=form.phone.data,
                email=form.email.data,
                website=form.website.data,
                food_type=form.food_type.data,
                has_wifi=form.has_wifi.data,
                has_tv=form.has_tv.data,
                has_ac=form.has_ac.data,
                has_minibar=form.has_minibar.data,
                has_safe=form.has_safe.data,
                has_balcony=form.has_balcony.data,
                has_pool=form.has_pool.data,
                has_spa=form.has_spa.data,
                has_entertainment=form.has_entertainment.data,
                photo_filename=filename,
                # Новые поля
                location_score=form.location_score.data,
                comfort_score=form.comfort_score.data,
                service_score=form.service_score.data,
                treatment_score=form.treatment_score.data,
                food_score=form.food_score.data,
                price_score=form.price_score.data,
                resort=form.resort.data,
                specialization=form.specialization.data,
                equipment=form.equipment.data,
                room_types=form.room_types.data,
                attractions_distance=form.attractions_distance.data
            )

            db.session.add(sanatorium)
            db.session.commit()
            flash('Санаторий успешно добавлен!', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'danger')

    return render_template('add_sanatorium.html', form=form)


@app.route('/edit_sanatorium/<int:id>', methods=['GET', 'POST'])
def edit_sanatorium(id):
    sanatorium = Sanatorium.query.get_or_404(id)
    form = SanatoriumForm(obj=sanatorium)  # Предзаполняем форму данными из БД

    if form.validate_on_submit():
        try:
            form.populate_obj(sanatorium)  # Обновляем объект данными из формы

            # Обработка загрузки нового фото
            if form.photo.data:
                photo_file = form.photo.data
                filename = secure_filename(photo_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # Обработка изображения
                image = Image.open(photo_file)
                image = image.convert('RGB')
                image.thumbnail((800, 600))
                image.save(file_path, format='JPEG', quality=85)

                sanatorium.photo_filename = filename

            db.session.commit()
            flash('Санаторий успешно обновлен!', 'success')
            return redirect(url_for('sanatorium_detail', id=sanatorium.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обновлении: {str(e)}', 'danger')

    return render_template('edit_sanatorium.html', form=form, sanatorium=sanatorium)


@app.route('/delete_sanatorium/<int:id>', methods=['POST'])
def delete_sanatorium(id):
    # Двойная проверка: авторизация + права администратора
    if 'user_id' not in session or not session.get('is_admin'):
        abort(403)

    sanatorium = Sanatorium.query.get_or_404(id)

    try:
        if sanatorium.photo_filename:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], sanatorium.photo_filename))
            except OSError:
                pass

        db.session.delete(sanatorium)
        db.session.commit()
        flash('Санаторий успешно удалён!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')

    return redirect(url_for('index'))


@app.route('/sanatorium/<int:id>')
def sanatorium_detail(id):
    sanatorium = Sanatorium.query.get_or_404(id)
    return render_template('sanatorium_detail.html', sanatorium=sanatorium)


if __name__ == '__main__':
    app.run(debug=True)
