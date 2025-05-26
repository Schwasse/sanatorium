from app import app, db

with app.app_context():
    db.create_all()
    print("Таблицы успешно созданы!")
def profile():
    print("OK")
    user_id = session['user_id']
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    form = UserProfileForm(obj=profile)

    if form.validate_on_submit():
        if not profile:
            profile = UserProfile(user_id=user_id)

        form.populate_obj(profile)
        profile.services = ','.join(form.services.data)  # сохраняем как строку

        db.session.add(profile)
        db.session.commit()
        flash("Профиль обновлён", "success")
        return redirect(url_for('index'))

    if profile:
        form.services.data = profile.services.split(',')  # преобразуем обратно

    return render_template("profile.html", form=form)