from flask import Blueprint, render_template, request, abort
from db.db import conn
from collections import defaultdict
from datetime import datetime, timedelta
import base64

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile/<int:trainer_id>', methods=['GET', 'POST'])
def profile(trainer_id):
    conn.ping(reconnect=True)  # 끊어진 연결 대비

    with conn.cursor() as cursor:
        # 트레이너 정보 가져오기
        cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
        trainer = cursor.fetchone()
        if not trainer:
            abort(404)

        # 트레이너 이미지 가져오기
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT image_data FROM site_images
                WHERE name LIKE %s
                ORDER BY uploaded_at ASC
            """, (f'트레이너{trainer_id}%',))
            image_rows = cursor.fetchall()

        # base64로 인코딩
        image_sources = []
        for row in image_rows:
            encoded = base64.b64encode(row['image_data']).decode('utf-8')
            image_sources.append(f"data:image/jpeg;base64,{encoded}")

        # 리뷰 작성 처리 (POST 요청)
        if request.method == 'POST':
            new_rating = int(request.form['rating'])
            new_text = request.form['review']
            user_id = 1  # 로그인 기능 붙이면 session에서 가져올 예정

            cursor.execute("""
                INSERT INTO reviews (user_id, trainer_id, rating, comment)
                VALUES (%s, %s, %s, %s)
            """, (user_id, trainer_id, new_rating, new_text))
            conn.commit()

        # 리뷰 목록 + 작성자 이름 가져오기
        cursor.execute("""
            SELECT r.rating, r.comment, r.created_at, u.login_id
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.trainer_id = %s
            ORDER BY r.created_at DESC
        """, (trainer_id,))
        reviews = cursor.fetchall()

    # 리뷰 통계 계산
    review_count = len(reviews)
    avg_rating = round(sum(r["rating"] for r in reviews) / review_count, 1) if review_count > 0 else 0.0

        # === 지난달 통계 계산 ===
    today = datetime.today()
    last_month = today.replace(day=1) - timedelta(days=1)
    year = last_month.year
    month = last_month.month

    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT gender, age_group, SUM(member_count) as count
            FROM trainer_member_stats
            WHERE trainer_id = %s AND year = %s AND month = %s
            GROUP BY gender, age_group
        """, (trainer_id, year, month))
        rows = cursor.fetchall()

    gender_counter = defaultdict(int)
    age_counter = defaultdict(int)
    total_count = 0

    for row in rows:
        gender_counter[row['gender']] += row['count']
        age_counter[row['age_group']] += row['count']
        total_count += row['count']

    gender_data = {k: round(v / total_count * 100, 1) for k, v in gender_counter.items()} if total_count else {}
    age_data = {k: round(v / total_count * 100, 1) for k, v in age_counter.items()} if total_count else {}

    is_admin = True  # 로그인 연동되면 조건에 따라 설정
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