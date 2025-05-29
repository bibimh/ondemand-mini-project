# profile_routes.py

from flask import Blueprint, render_template, request, abort, redirect, session, url_for
from db.db import conn
from collections import defaultdict
from datetime import datetime
import base64

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile/<int:trainer_id>', methods=['GET', 'POST'])
def profile(trainer_id):
    conn.ping(reconnect=True)  # 끊어진 연결 대비

    # 세션 확인
    user_id = session.get('user_id')

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
        trainer = cursor.fetchone()
        if not trainer:
            abort(404)

        # === 이미지 가져오기 ===
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

    # === 리뷰 처리 ===
    with conn.cursor() as cursor:
        # === 리뷰 작성 (POST 요청 시) ===
        if request.method == 'POST':
            if not user_id:
                return redirect(url_for('login'))

            # 이 사용자가 이 트레이너에게 등록한 적이 있는지 확인
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM member_regist
                WHERE user_id = %s AND trainer_id = %s
            """, (user_id, trainer_id))
            is_registered = cursor.fetchone()['cnt'] > 0

            if not is_registered:
                return "<h3>해당 트레이너는 회원님의 담당 트레이너가 아닙니다. 리뷰를 작성할 수 없습니다.</h3>"

            # 작성 처리
            new_rating = int(request.form['rating'])
            new_text = request.form['review']

            cursor.execute("""
                INSERT INTO reviews (user_id, trainer_id, rating, comment)
                VALUES (%s, %s, %s, %s)
            """, (user_id, trainer_id, new_rating, new_text))
            conn.commit()
            return redirect(url_for('profile.profile', trainer_id=trainer_id))
        
        # 리뷰 조회 쿼리
        cursor.execute("""
            SELECT r.review_id, r.user_id, r.rating, r.comment, r.created_at, u.login_id
            FROM reviews r JOIN users u ON r.user_id = u.user_id
            WHERE r.trainer_id = %s
            ORDER BY r.created_at DESC
        """, (trainer_id,))
        reviews = cursor.fetchall()

    # 리뷰 통계 계산
    review_count = len(reviews)
    avg_rating = round(sum(r["rating"] for r in reviews) / review_count, 1) if review_count > 0 else 0.0

    # === 이 유저가 등록한 트레이너인지 확인 (템플릿 전달용)
    is_registered = False
    if user_id:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM member_regist
                WHERE user_id = %s AND trainer_id = %s
            """, (user_id, trainer_id))
            is_registered = cursor.fetchone()['cnt'] > 0

    # === 지난달 성별 통계 ===
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
        gender_rows = cursor.fetchall()
        for row in gender_rows:
            gender_counter[row['gender']] += row['count']
            total_count += row['count']

    # === 지난달 연령대 통계 ===
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
        age_rows = cursor.fetchall()

        for row in age_rows:
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

    gender_data = {
        k: round(v / total_count * 100, 1) for k, v in gender_counter.items()
    } if total_count else {}

    age_data = {
        k: round(v / total_count * 100, 1) for k, v in age_counter.items()
    } if total_count else {k: 0.0 for k in age_groups}

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
        is_admin=session.get('is_admin') == 1,
        is_registered=is_registered
    )

@profile_bp.route('/profile/<int:trainer_id>/delete_review', methods=['POST'])
def delete_review(trainer_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    review_id = request.form.get('review_id')
    user_id = session['user_id']

    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM reviews WHERE review_id = %s AND user_id = %s", (review_id, user_id))
        conn.commit()

    return redirect(url_for('profile.profile', trainer_id=trainer_id))