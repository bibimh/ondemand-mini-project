from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from profile_routes import profile_bp
from profile_edit_routes import edit_profile_bp
from mainpage_route import mainpage_bp
from consultation_routes import consultation_bp
from db.db import get_all_trainers
import io
import pymysql

app = Flask(__name__)
app.secret_key = 'a9f3b7d2e1c4f6a8'

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

# 트레이너 매칭 라우트
@app.route('/match', methods=['GET', 'POST'])
def match_trainer():
    user_id = session.get('user_id')

    if request.method == 'POST':
        trait_1 = request.form['trait_1']
        trait_2 = request.form['trait_2']
        trait_3 = request.form['trait_3']
        trait_4 = request.form['trait_4']
        trait_5 = request.form['trait_5']

        if user_id:
            conn = get_db()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_answers (user_id, trait_1, trait_2, trait_3, trait_4, trait_5)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (user_id, trait_1, trait_2, trait_3, trait_4, trait_5))
                conn.commit()
        else:
            session['pending_traits'] = {
                'trait_1': trait_1,
                'trait_2': trait_2,
                'trait_3': trait_3,
                'trait_4': trait_4,
                'trait_5': trait_5,
            }

        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT trainer_id, tname, image_id, (
                    (trait_1 = %s) + (trait_2 = %s) + (trait_3 = %s) +
                    (trait_4 = %s) + (trait_5 = %s)
                ) AS match_score
                FROM trainers
                ORDER BY match_score DESC
                LIMIT 1
            """, (trait_1, trait_2, trait_3, trait_4, trait_5))
            best_match = cursor.fetchone()

        return render_template('match_result.html', trainer=best_match)

    return render_template('match_form.html')

# 로그인 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    login_id = request.form['login_id']
    password = request.form['password']

    if not login_id or not password:
        return jsonify({'success': False, 'message': '모든 정보를 입력해주세요.'})

    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE login_id = %s", (login_id,))
        user = cursor.fetchone()

    if not user:
        return jsonify({'success': False, 'message': '없는 아이디입니다.'})
    elif not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'message': '비밀번호를 확인해주세요.'})
    else:
        session['user_id'] = user['user_id']
        session['uname'] = user['uname']
        session['is_admin'] = user['is_admin']

        if 'pending_traits' in session:
            traits = session.pop('pending_traits')
            with get_db() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO user_answers (user_id, trait_1, trait_2, trait_3, trait_4, trait_5)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (user['user_id'], traits['trait_1'], traits['trait_2'], traits['trait_3'], traits['trait_4'], traits['trait_5']))
                    conn.commit()

        redirect_url = '/admin' if user['is_admin'] else '/'
        return jsonify({'success': True, 'redirect': redirect_url})

# 이미지 불러오기 라우트 (중복 제거됨)
@app.route('/image/<int:image_id>')
def get_image(image_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT image_data, mimetype FROM site_images WHERE image_id = %s", (image_id,))
        row = cursor.fetchone()
        if row and row['image_data']:
            return send_file(
                io.BytesIO(row['image_data']),
                mimetype=row['mimetype'] or 'image/jpeg'
            )
    return 'Image Not Found', 404

# 회원가입 라우트
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    login_id = request.form['login_id']
    password = request.form['password']
    confirm = request.form['confirm_password']
    uname = request.form['uname']
    phone = request.form['phone']
    gender = request.form.get('gender')
    birthday = request.form['birthday']

    if not login_id:
        return jsonify({'success': False, 'field': 'id', 'message': '아이디를 입력해주세요.'})
    if not password:
        return jsonify({'success': False, 'field': 'password', 'message': '비밀번호를 입력해주세요.'})
    if not confirm:
        return jsonify({'success': False, 'field': 'confirm-password', 'message': '비밀번호 확인을 입력해주세요.'})
    if not uname:
        return jsonify({'success': False, 'field': 'name', 'message': '이름을 입력해주세요.'})
    if not phone:
        return jsonify({'success': False, 'field': 'phone', 'message': '연락처를 입력해주세요.'})
    if not gender:
        return jsonify({'success': False, 'field': 'gender', 'message': '성별을 선택해주세요.'})
    if not birthday:
        return jsonify({'success': False, 'field': 'birthday', 'message': '생년월일을 입력해주세요.'})
    if password != confirm:
        return jsonify({'success': False, 'field': 'confirm-password', 'message': '비밀번호가 일치하지 않습니다.'})
    if len(login_id) < 6 or len(login_id) > 20:
        return jsonify({'success': False, 'field': 'id', 'message': '아이디는 6~20자여야 합니다.'})

    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM users WHERE login_id = %s", (login_id,))
        if cursor.fetchone():
            return jsonify({'success': False, 'field': 'id', 'message': '이미 있는 아이디입니다.'})

        password_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (login_id, password_hash, uname, phone, gender, birthday)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (login_id, password_hash, uname, phone, gender, birthday))
        conn.commit()

    return jsonify({'success': True, 'message': '회원가입이 완료되었습니다. 로그인해주세요.'})

# 로그아웃 라우트
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 트레이너 프로필 상세 페이지
@app.route('/trainer/<int:trainer_id>')
def trainer_profile(trainer_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
        trainer = cursor.fetchone()
    return render_template('trainer_profile.html', trainer=trainer)

# 관리자 전용 예약 조회 페이지
@app.route('/admin/consultations')
def admin_consultations():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect('/')

    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT 
                r.reservation_id, r.user_id, r.trainer_id, r.reservation_date,
                r.reservation_time, r.num_people, r.status, r.created_at,
                t.tname AS trainer_name, t.image_id,
                u.uname AS user_name, u.phone AS user_phone
            FROM reservations r
            JOIN trainers t ON r.trainer_id = t.trainer_id
            JOIN users u ON r.user_id = u.user_id
            ORDER BY r.created_at DESC
        """)
        reservations = cursor.fetchall()

        for r in reservations:
            if hasattr(r['reservation_time'], 'total_seconds'):
                sec = int(r['reservation_time'].total_seconds())
                r['reservation_time_str'] = f"{sec//3600:02}:{(sec%3600)//60:02}"
            else:
                r['reservation_time_str'] = str(r['reservation_time'])[:5]

        cursor.execute("SELECT COUNT(*) as total FROM reservations")
        total_count = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as today FROM reservations WHERE reservation_date = CURDATE()")
        today_count = cursor.fetchone()['today']

        cursor.execute("""
            SELECT COUNT(*) as month 
            FROM reservations 
            WHERE reservation_date >= DATE_FORMAT(NOW(), '%Y-%m-01')
        """)
        month_count = cursor.fetchone()['month']

        cursor.execute("SELECT COUNT(*) as active FROM trainers WHERE is_hidden = 0")
        active_trainers = cursor.fetchone()['active']

        cursor.execute("SELECT trainer_id, tname FROM trainers WHERE is_hidden = 0")
        trainers = cursor.fetchall()

    return render_template('admin_consultations.html',
                           reservations=reservations,
                           total_count=total_count,
                           today_count=today_count,
                           month_count=month_count,
                           active_trainers=active_trainers,
                           trainers=trainers)

# 블루프린트 등록
app.register_blueprint(profile_bp)
app.register_blueprint(edit_profile_bp)
app.register_blueprint(mainpage_bp)
app.register_blueprint(consultation_bp)

# 앱 실행
if __name__ == '__main__':
    app.run(debug=True)
