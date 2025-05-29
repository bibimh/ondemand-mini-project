from flask import Blueprint, render_template, request, abort, redirect, url_for
from db.db import get_db
from collections import defaultdict
from datetime import datetime
import base64

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile/<int:trainer_id>', methods=['GET', 'POST'])
def profile(trainer_id):
    with get_db() as conn:
        conn.ping(reconnect=True)

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
            trainer = cursor.fetchone()
            if not trainer:
                abort(404)

            cursor.execute("""
                SELECT image_data FROM site_images
                WHERE name LIKE %s
                ORDER BY uploaded_at ASC
            """, (f"trainer{trainer_id}%",))
            image_rows = cursor.fetchall()

        image_sources = [
            f"data:image/jpeg;base64,{base64.b64encode(row['image_data']).decode('utf-8')}"
            for row in image_rows
        ]

        with conn.cursor() as cursor:
            if request.method == 'POST':
                new_rating = int(request.form['rating'])
                new_text = request.form['review']
                user_id = 1

                cursor.execute("""
                    INSERT INTO reviews (user_id, trainer_id, rating, comment)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, trainer_id, new_rating, new_text))
                conn.commit()

                return redirect(url_for('profile.profile', trainer_id=trainer_id))

            cursor.execute("""
                SELECT r.rating, r.comment, r.created_at, u.login_id
                FROM reviews r JOIN users u ON r.user_id = u.user_id
                WHERE r.trainer_id = %s
                ORDER BY r.created_at DESC
            """, (trainer_id,))
            reviews = cursor.fetchall()

        review_count = len(reviews)
        avg_rating = round(sum(r["rating"] for r in reviews) / review_count, 1) if review_count > 0 else 0.0

        gender_counter = defaultdict(int)
        total_count = 0
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.gender, COUNT(*) as count
                FROM member_regist m
                JOIN users u ON m.user_id = u.user_id
                WHERE m.trainer_id = %s
                  AND m.regist_date BETWEEN DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH, '%%Y-%%m-01')
                  AND LAST_DAY(CURDATE() - INTERVAL 1 MONTH)
                GROUP BY u.gender
            """, (trainer_id,))
            for row in cursor.fetchall():
                gender_counter[row['gender']] += row['count']
                total_count += row['count']

        age_groups = ['10대', '20대', '30대', '40대', '50대+']
        age_counter = {group: 0 for group in age_groups}

        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT FLOOR(TIMESTAMPDIFF(YEAR, u.birthday, CURDATE()) / 10) * 10 AS age_group, COUNT(*) AS count
                FROM member_regist m
                JOIN users u ON m.user_id = u.user_id
                WHERE m.trainer_id = %s
                  AND m.regist_date BETWEEN DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH, '%%Y-%%m-01')
                  AND LAST_DAY(CURDATE() - INTERVAL 1 MONTH)
                GROUP BY age_group
                ORDER BY age_group
            """, (trainer_id,))
            for row in cursor.fetchall():
                decade = row['age_group']
                count = row['count']
                if decade < 10:
                    continue
                elif decade >= 50:
                    age_counter['50대+'] += count
                else:
                    label = f"{decade}대"
                    if label in age_counter:
                        age_counter[label] += count

        gender_data = {k: round(v / total_count * 100, 1) for k, v in gender_counter.items()} if total_count else {}
        age_data = {k: round(v / total_count * 100, 1) for k, v in age_counter.items()} if total_count else {k: 0.0 for k in age_groups}

        return render_template(
            'profile.html',
            trainer=trainer,
            trainer_id=trainer_id,
            reviews=reviews,
            avg_rating=avg_rating,
            review_count=review_count,
            gender_data=gender_data,
            age_data=age_data,
            image_sources=image_sources,
            is_admin=True
        )
