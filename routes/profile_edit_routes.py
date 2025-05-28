# profile_edit_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, abort
from db.db import conn
from datetime import datetime
import base64

edit_profile_bp = Blueprint('edit_profile', __name__)

@edit_profile_bp.route('/profile/<int:trainer_id>/edit', methods=['GET', 'POST'])
def edit_profile(trainer_id):
    conn.ping(reconnect=True)

    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
        trainer = cursor.fetchone()

        cursor.execute("SELECT name, image_data FROM site_images WHERE name LIKE %s", (f"트레이너{trainer_id}_%",))
        image_rows = cursor.fetchall()

    image_sources = [{
        'name': row['name'],
        'src': f"data:image/jpeg;base64,{base64.b64encode(row['image_data']).decode('utf-8')}"
    } for row in image_rows]

    if request.method == 'POST':
        # 이름, 소개글, 성별 저장
        tname = request.form['tname']
        introduce = request.form['introduce']
        trait_5 = request.form['trait_5']
        mbti = request.form['mbti'].upper()

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE trainers SET tname=%s, introduce=%s,
                trait_1=%s, trait_2=%s, trait_3=%s, trait_4=%s, trait_5=%s
            WHERE trainer_id = %s
        """, (tname, introduce, mbti[0], mbti[1], mbti[2], mbti[3], trait_5, trainer_id))

        # 이미지 삭제 처리
        delete_images = request.form.getlist('delete_images')
        for name in delete_images:
            cursor.execute("DELETE FROM site_images WHERE name = %s", (name,))

        # 이미지 추가
        new_files = request.files.getlist('new_images')
        cursor.execute("SELECT COUNT(*) as count FROM site_images WHERE name LIKE %s", (f"%트레이너{trainer_id}_%",))
        existing_count = cursor.fetchone()['count']

        for i, file in enumerate(new_files):
            if file and file.filename:
                name = f"트레이너{trainer_id}_{existing_count + i + 1}"
                data = file.read()
                cursor.execute("""
                    INSERT INTO site_images (name, image_data, description)
                    VALUES (%s, %s, %s)
                """, (name, data, '프로필 이미지'))

        conn.commit()
        return redirect(url_for('profile.profile', trainer_id=trainer_id))

    return render_template('edit_profile.html', trainer=trainer, trainer_id=trainer_id, image_sources=image_sources)