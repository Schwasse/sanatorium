from flask import current_app
from models import db, Sanatorium, UserProfile
import json
import numpy as np
from models import UserProfile, Sanatorium
import ast


def evaluate_sanatoriums(user_id):
    """Расширенная оценка санаториев с улучшенной обработкой данных и возвратом правильного формата"""
    try:
        current_app.logger.info(f"Начало оценки санаториев для user_id: {user_id}")

        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            current_app.logger.error("Профиль не найден")
            return None

        if not profile.criteria_weights:
            current_app.logger.error("Отсутствуют criteria_weights в профиле")
            return None

        weights = profile.criteria_weights

        # Преобразование строки JSON в dict
        if isinstance(weights, str):
            try:
                weights = json.loads(weights)
            except json.JSONDecodeError:
                current_app.logger.error("Ошибка декодирования JSON criteria_weights")
                return None

        # Если numpy array
        if hasattr(weights, 'tolist'):
            weights = weights.tolist()
            criteria_names = ['price', 'comfort', 'treatment', 'location', 'service']
            if len(weights) != len(criteria_names):
                current_app.logger.error("Размерность весов не совпадает с количеством критериев")
                return None
            weights = {name: float(weight) for name, weight in zip(criteria_names, weights)}

        if not isinstance(weights, dict):
            current_app.logger.error(f"Неправильный формат весов: {type(weights)}")
            return None

        current_app.logger.info(f"Используемые веса: {weights}")

        recommendations = []

        for sanatorium in Sanatorium.query.all():
            try:
                criteria_scores = {
                    "price": sanatorium.price_score,
                    "comfort": sanatorium.comfort_score,
                    "treatment": sanatorium.treatment_score,
                    "location": sanatorium.location_score,
                    "service": sanatorium.service_score,
                }

                total_score = sum(
                    criteria_scores[crit] * weights.get(crit, 0)
                    for crit in criteria_scores
                )

                normalized_score = round((total_score / 5) * 100, 1)  # Приводим к шкале 0-100

                recommendations.append({
                    "sanatorium": sanatorium,
                    "normalized_score": normalized_score,
                    "criteria_scores": criteria_scores
                })

            except Exception as e:
                current_app.logger.error(f"Ошибка при оценке санатория {sanatorium.id}: {str(e)}")

        recommendations.sort(key=lambda x: x["normalized_score"], reverse=True)
        return recommendations[:10]

    except Exception as e:
        current_app.logger.error(f"Ошибка в evaluate_sanatoriums: {str(e)}", exc_info=True)
        return None

def calculate_match_percentage(self, profile, sanatorium):
    """Расчет процента соответствия санатория профилю пользователя"""
    match_score = 0
    max_score = 0

    # Соответствие региона
    if profile.region:
        max_score += 1
        if sanatorium.region == profile.region:
            match_score += 1

    # Соответствие типа
    if profile.sanatorium_type:
        max_score += 1
        if sanatorium.sanatorium_type == profile.sanatorium_type:
            match_score += 1

    # Соответствие услуг
    if profile.services:
        needed_services = set(profile.services.split(','))
        available_services = set((sanatorium.services or '').split(','))
        max_score += len(needed_services)
        match_score += len(needed_services & available_services)

    # Соответствие бюджету
    if profile.budget:
        max_score += 1
        if sanatorium.price_per_night <= profile.budget * 1.1:  # +10% допуск
            match_score += 1

    return round((match_score / max_score) * 100) if max_score > 0 else 0

import numpy as np
from models import Sanatorium, UserProfile
from flask import current_app
import random


def auto_score_sanatoriums():
    """Автоматическая генерация оценок для санаториев"""
    try:
        for san in Sanatorium.query.all():
            san.location_score = round(random.uniform(3.0, 5.0), 1)
            san.comfort_score = round(random.uniform(3.0, 5.0), 1)
            san.service_score = round(random.uniform(3.0, 5.0), 1)
            san.treatment_score = round(random.uniform(3.0, 5.0), 1)
            san.food_score = round(random.uniform(3.0, 5.0), 1)
            # Для цены - чем дешевле, тем лучше (обратная зависимость)
            san.price_score = round(random.uniform(1.0, 5.0 - (san.price_per_night / 5000)), 1)

        db.session.commit()
        current_app.logger.info("Автоматические оценки санаториев успешно сгенерированы")
    except Exception as e:
        current_app.logger.error(f"Ошибка генерации оценок: {str(e)}")
        db.session.rollback()