# profile_edit_routes.py

from flask import Blueprint, session, render_template, request, redirect, url_for, abort
import pymysql
from datetime import datetime
import base64
import re

edit_profile_bp = Blueprint('edit_profile', __name__)

# DB 연결 함수
def get_db():
    return pymysql.connect(
        host='192.168.40.14',
        user='fitpickuser',
        password='fitpick1234',
        db='fitpick',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@edit_profile_bp.route('/profile/<int:trainer_id>/edit', methods=['GET', 'POST'])
def edit_profile(trainer_id):
    conn = get_db()
    try:
        if request.method == 'POST':
            tname = request.form.get('tname', '')
            introduce = request.form.get('introduce', '')
            mbti = request.form.get('mbti', '').upper()

            # 성별 매핑
            gender_input = request.form.get('trait_5', '')  # '남성' or '여성'
            trait_5 = '남' if gender_input == '남성' else '여'  # trait_5는 '남' 또는 '여'
            gender_code = 'M' if trait_5 == '남' else 'F'  # gender는 'M' 또는 'F'

            # MBTI 유효성 검사
            VALID_MBTIS = {
                "ISTJ", "ISFJ", "INFJ", "INTJ",
                "ISTP", "ISFP", "INFP", "INTP",
                "ESTP", "ESFP", "ENFP", "ENTP",
                "ESTJ", "ESFJ", "ENFJ", "ENTJ"
            }

            if mbti not in VALID_MBTIS:
                # MBTI가 유효하지 않으면 다시 trainer/image_sources 가져오기
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
                    trainer = cursor.fetchone()

                    cursor.execute("SELECT name, image_data FROM site_images WHERE name LIKE %s", (f"trainer{trainer_id}_%",))
                    image_rows = cursor.fetchall()

                image_sources = [
                    {
                        'name': row['name'],
                        'src': f"data:image/jpeg;base64,{base64.b64encode(row['image_data']).decode('utf-8')}"
                    }
                    for row in image_rows
                ]

                return render_template(
                    'edit_profile.html',
                    trainer=trainer,
                    trainer_id=trainer_id,
                    image_sources=image_sources,
                    error_message="MBTI 입력 오류"
                )
            
            # MBTI 정상일 경우 -> DB 업데이트
            with conn.cursor() as cursor:
                # 트레이너 정보 수정
                cursor.execute("""
                    UPDATE trainers SET
                        tname = %s,
                        introduce = %s,
                        trait_1 = %s,
                        trait_2 = %s,
                        trait_3 = %s,
                        trait_4 = %s,
                        trait_5 = %s,
                        gender = %s
                    WHERE trainer_id = %s
                """, (
                    tname, introduce,
                    mbti[0], mbti[1], mbti[2], mbti[3],
                    trait_5, gender_code, trainer_id
                ))

                # 삭제할 이미지 처리
                delete_images = request.form.getlist('delete_images')
                for name in delete_images:
                    cursor.execute("DELETE FROM site_images WHERE name = %s", (name,))

                # 새 이미지 추가
                new_files = request.files.getlist('new_images')
                # 기존 이름들 가져오기
                cursor.execute("SELECT name FROM site_images WHERE name LIKE %s", (f"trainer{trainer_id}_%",))
                existing_names = cursor.fetchall()

                # 가장 높은 번호 구하기
                import re
                max_index = 0
                for row in existing_names:
                    match = re.match(rf'trainer{trainer_id}_(\d+)', row['name'])
                    if match:
                        index = int(match.group(1))
                        if index > max_index:
                            max_index = index

                # 새 이미지 추가
                new_files = request.files.getlist('new_images')
                for i, file in enumerate(new_files):
                    if file and file.filename:
                        name = f"trainer{trainer_id}_{max_index + i + 1}"  # ✅ 여기에서 기존 변수명만 바꿔주면 OK
                        data = file.read()
                        cursor.execute("""
                            INSERT INTO site_images (name, image_data, description)
                            VALUES (%s, %s, %s)
                        """, (name, data, '프로필 이미지'))

                conn.commit()

            return redirect(url_for('profile.profile', trainer_id=trainer_id))

        # ===== GET 요청 처리 =====
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
            trainer = cursor.fetchone()

            cursor.execute("SELECT name, image_data FROM site_images WHERE name LIKE %s", (f"trainer{trainer_id}_%",))
            image_rows = cursor.fetchall()

        image_sources = [
            {
                'name': row['name'],
                'src': f"data:image/jpeg;base64,{base64.b64encode(row['image_data']).decode('utf-8')}"
            }
            for row in image_rows
        ]

        return render_template(
            'edit_profile.html',
            trainer=trainer,
            trainer_id=trainer_id,
            image_sources=image_sources
        )
    
    finally:
        conn.close()  # 반드시 연결 닫기

@edit_profile_bp.route('/profile/<int:trainer_id>/delete', methods=['GET'])
def delete_profile(trainer_id):
    if session.get('is_admin') != 1:
        abort(403)
        
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 트레이너 삭제
            cursor.execute("DELETE FROM trainers WHERE trainer_id = %s", (trainer_id,))
            # 이미지도 삭제
            cursor.execute("DELETE FROM site_images WHERE name LIKE %s", (f"trainer{trainer_id}%",))
            conn.commit()
    finally:
        conn.close()

    return redirect('/')  # 삭제 후 메인 페이지로 이동