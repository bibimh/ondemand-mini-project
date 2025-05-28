from flask import Blueprint, render_template, request, abort
from db.db import conn
from collections import defaultdict
from datetime import datetime, timedelta
import base64
from flask import redirect, url_for

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile/<int:trainer_id>', methods=['GET', 'POST'])
def profile(trainer_id):
    conn.ping(reconnect=True)  # 끊어진 연결 대비

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
        """, (f"%트레이너{trainer_id}%",))
        image_rows = cursor.fetchall()

    image_sources = [
        f"data:image/jpeg;base64,{base64.b64encode(row['image_data']).decode('utf-8')}"
        for row in image_rows
    ]

    # === 리뷰 처리 ===
    with conn.cursor() as cursor:
        if request.method == 'POST':
            new_rating = int(request.form['rating'])
            new_text = request.form['review']
            user_id = 1  # 임시 사용자

            cursor.execute("""
                INSERT INTO reviews (user_id, trainer_id, rating, comment)
                VALUES (%s, %s, %s, %s)
            """, (user_id, trainer_id, new_rating, new_text))
            conn.commit()

            # 중복 방지를 위해 GET으로 리다이렉트
            return redirect(url_for('profile.profile', trainer_id=trainer_id))
        
        cursor.execute("""
            SELECT r.rating, r.comment, r.created_at, u.login_id
            FROM reviews r JOIN users u ON r.user_id = u.user_id
            WHERE r.trainer_id = %s
            ORDER BY r.created_at DESC
        """, (trainer_id,))
        reviews = cursor.fetchall()

    # 리뷰 통계 계산
    review_count = len(reviews)
    avg_rating = round(sum(r["rating"] for r in reviews) / review_count, 1) if review_count > 0 else 0.0

    # === 지난달 통계 계산 (gender만 출력, 연령대는 임시 미사용) ===
    today = datetime.today()
    first_day_this_month = today.replace(day=1)
    last_month_end = first_day_this_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT u.gender, COUNT(*) as count
            FROM member_regist m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.trainer_id = %s
              AND m.regist_date BETWEEN %s AND %s
            GROUP BY u.gender
        """, (trainer_id, last_month_start.date(), last_month_end.date()))
        rows = cursor.fetchall()

    gender_counter = defaultdict(int)
    age_counter = defaultdict(int)  # 빈 dict 유지
    total_count = 0

    for row in rows:
        gender = row['gender']
        count = row['count']
        gender_counter[gender] += count
        total_count += count

    gender_data = {k: round(v / total_count * 100, 1) for k, v in gender_counter.items()} if total_count else {}
    age_data = {k: round(v / total_count * 100, 1) for k, v in age_counter.items()} if total_count else {}

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