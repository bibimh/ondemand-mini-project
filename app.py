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

# 트레이너 매칭 라우트 (수정됨)
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
            conn.close()
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
            # 매칭 점수를 계산하여 가장 높은 트레이너를 찾는 쿼리
            # 각 trait가 일치하는 경우 1점씩 부여하고, 총합을 match_score로 계산
            # 이 점수를 20배하여 match_percentage로 변환
            # match_score는 0~5 사이의 값이므로, match_percentage는 0~100 사이가 됨
            cursor.execute("""
                SELECT trainer_id, tname, trainer_id as image_id,
                (
                    (trait_1 = %s) + (trait_2 = %s) + (trait_3 = %s) +
                    (trait_4 = %s) + (trait_5 = %s)
                ) AS match_score,
                ROUND((
                    (trait_1 = %s) + (trait_2 = %s) + (trait_3 = %s) +
                    (trait_4 = %s) + (trait_5 = %s)
                ) * 20, 0) AS match_percentage
                FROM trainers
                WHERE is_hidden = 0
                ORDER BY match_score DESC
                LIMIT 1
            """, (
                trait_1, trait_2, trait_3, trait_4, trait_5, 
                trait_1, trait_2, trait_3, trait_4, trait_5  
            ))
            best_match = cursor.fetchone()
        conn.close()

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
    try:
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

            # pending_traits 저장된 경우 사용자 답변 테이블에 저장
            if 'pending_traits' in session:
                traits = session.pop('pending_traits')
                with conn.cursor() as cursor:  # 기존 conn 재사용
                    cursor.execute("""
                        INSERT INTO user_answers (user_id, trait_1, trait_2, trait_3, trait_4, trait_5)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        user['user_id'],
                        traits['trait_1'], traits['trait_2'],
                        traits['trait_3'], traits['trait_4'], traits['trait_5']
                    ))
                    conn.commit()

            # 로그인 후 이동할 URL 설정
            next_url = request.args.get('next')
            if next_url:
                redirect_url = next_url
            elif user['is_admin']:
                redirect_url = '/admin/consultations'
            else:
                redirect_url = '/'

            return jsonify({'success': True, 'redirect': redirect_url})

    except Exception as e:
        print(f"[로그인 오류] {e}")
        return jsonify({'success': False, 'message': '서버 내부 오류가 발생했습니다.'})
    finally:
        conn.close()


# 이미지 불러오기 라우트 (수정된 버전)
@app.route('/image/<int:image_id>')
def get_image(image_id):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 1차: image_id 직접 조회
            cursor.execute("SELECT image_data FROM site_images WHERE image_id = %s", (image_id,))
            row = cursor.fetchone()
            if row and row['image_data']:
                return send_file(io.BytesIO(row['image_data']), mimetype='image/jpeg')

            # 2차: trainer_id로 추정해서 이름 패턴으로 조회
            cursor.execute("""
                SELECT image_data 
                FROM site_images 
                WHERE name LIKE %s 
                ORDER BY uploaded_at ASC 
                LIMIT 1
            """, (f"trainer{image_id}_%",))
            row = cursor.fetchone()
            if row and row['image_data']:
                return send_file(io.BytesIO(row['image_data']), mimetype='image/jpeg')

            # 3차: 기본 이미지 반환 (image_id=48)
            cursor.execute("SELECT image_data FROM site_images WHERE image_id = 48")
            row = cursor.fetchone()
            if row and row['image_data']:
                return send_file(io.BytesIO(row['image_data']), mimetype='image/jpeg')

    finally:
        conn.close()

    return 'Image Not Found', 404

# 트레이너 전용 이미지 라우트 추가
@app.route('/trainer-image/<int:trainer_id>')
def get_trainer_image(trainer_id):
    """트레이너 ID로 해당 트레이너의 첫 번째 이미지를 가져오고, 없으면 기본 이미지 반환"""
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            # 1차: trainer{ID}_ 로 시작하는 이미지 검색
            cursor.execute("""
                SELECT image_data 
                FROM site_images 
                WHERE name LIKE %s 
                ORDER BY uploaded_at ASC 
                LIMIT 1
            """, (f"trainer{trainer_id}_%",))
            row = cursor.fetchone()
            if row and row['image_data']:
                return send_file(io.BytesIO(row['image_data']), mimetype='image/jpeg')

            # 2차: 기본 이미지 (image_id=48) 가져오기
            cursor.execute("SELECT image_data FROM site_images WHERE image_id = 48")
            row = cursor.fetchone()
            if row and row['image_data']:
                return send_file(io.BytesIO(row['image_data']), mimetype='image/jpeg')

    finally:
        conn.close()

    return 'Image Not Found', 404

    
    # 기본 이미지 반환 (image_id=48 또는 1)
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT image_data FROM site_images WHERE image_id = %s", (48,))
            row = cursor.fetchone()
            if row and row['image_data']:
                return send_file(
                    io.BytesIO(row['image_data']),
                    mimetype='image/jpeg'
                )
    finally:
        conn.close()
        
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
    try:
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
    finally:
        conn.close()

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
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
            trainer = cursor.fetchone()
    finally:
        conn.close()
    return render_template('trainer_profile.html', trainer=trainer)

# 블루프린트 등록
app.register_blueprint(profile_bp)
app.register_blueprint(edit_profile_bp)
app.register_blueprint(mainpage_bp)
app.register_blueprint(consultation_bp)

# 앱 실행
if __name__ == '__main__':
    app.run(debug=True)