from flask import Blueprint, render_template, request, abort
from db.db import conn

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
            SELECT r.rating, r.comment, u.login_id
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.trainer_id = %s
            ORDER BY r.created_at DESC
        """, (trainer_id,))
        reviews = cursor.fetchall()

    # 리뷰 통계 계산
    review_count = len(reviews)
    avg_rating = round(sum(r["rating"] for r in reviews) / review_count, 1) if review_count > 0 else 0.0


    is_admin = True  # 로그인 연동되면 조건에 따라 설정
    return render_template(
        'profile.html', 
        trainer=trainer,
        trainer_id=trainer_id,
        reviews=reviews,
        avg_rating=avg_rating,
        review_count=review_count,
        is_admin=True
    )