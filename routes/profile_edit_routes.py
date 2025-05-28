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
        if not trainer:
            abort(404)

        if request.method == 'POST':
            new_intro = request.form['introduce']
            cursor.execute("UPDATE trainers SET introduce = %s WHERE trainer_id = %s", (new_intro, trainer_id))

            # 이미지 업로드 처리
            files = request.files.getlist('images')
            cursor.execute("SELECT COUNT(*) as count FROM site_images WHERE name LIKE %s", (f"%트레이너{trainer_id}_%",))
            existing_count = cursor.fetchone()['count']
            for i, file in enumerate(files):
                if file and file.filename:
                    image_data = file.read()
                    name = f"트레이너{trainer_id}_{existing_count + i + 1}"
                    cursor.execute("""
                        INSERT INTO site_images (name, image_data, description)
                        VALUES (%s, %s, %s)
                    """, (name, image_data, '프로필 이미지'))

            conn.commit()
            return redirect(url_for('profile.profile', trainer_id=trainer_id))

    return render_template('edit_profile.html', trainer=trainer, trainer_id=trainer_id)
