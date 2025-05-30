from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
from profile_routes import profile_bp
from profile_edit_routes import edit_profile_bp
from mainpage_route import mainpage_bp
from consultation_routes import consultation_bp
from config import logging, setup_logging
from utils.log_utils import log_user_action, log_admin_action
import io
import pymysql

setup_logging()

app = Flask(__name__)
app.secret_key = 'a9f3b7d2e1c4f6a8'

# DB 연결
def get_db():
    return pymysql.connect(
        host='192.168.40.14',
        user='fitpickuser',
        password='fitpick1234',
        db='fitpick',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
# 연결 확인 코드 
if __name__ == "__main__":
    try:
        conn = get_db()
        print("DB 연결 성공")
    except Exception as e:
        print(f"DB 연결 실패: {e}")
    finally:
        if conn:
            conn.close()
            print("DB 연결 종료")
            conn = None
# 로그인 페이지
@app.route('/')
def home():
    # log_admin_action(admin_id=session['admin_id'], action='관리자 대시보드 접속')
    log_admin_action(action='로그인 페이지 접속') 
    return render_template('login.html')

# 로그인 페이지 (GET), 로그인 처리 (POST)
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
        redirect_url = '/admin' if user['is_admin'] else '/info'
        return jsonify({'success': True, 'redirect': redirect_url})

# 회원가입 페이지 (GET), 회원가입 처리 (POST)
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

    # 필수 값 검사
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

    # 비밀번호 일치 확인
    if password != confirm:
        return jsonify({'success': False, 'field': 'confirm-password', 'message': '비밀번호가 일치하지 않습니다.'})

    # 아이디 길이 제한
    if len(login_id) < 6 or len(login_id) > 20:
        return jsonify({'success': False, 'field': 'id', 'message': '아이디는 6~20자여야 합니다.'})

    # 아이디 중복 검사
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


# 관리자 메인
@app.route('/admin')
def admin_page():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect('/')
    return f"<h1>관리자 페이지입니다, {session['uname']}님</h1>"

# 일반 사용자 메인
@app.route('/main')
def main_page():
    if 'user_id' not in session:
        return redirect('/')
    return f"<h1>환영합니다, {session['uname']}님!</h1>"

# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/info')

# 트레이너 매칭
@app.route('/match', methods=['GET', 'POST'])
def match_trainer():
    if 'user_id' not in session:
        return redirect('/')

    if request.method == 'POST':
        trait_1 = request.form['trait_1']
        trait_2 = request.form['trait_2']
        trait_3 = request.form['trait_3']
        trait_4 = request.form['trait_4']
        trait_5 = request.form['trait_5']

        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_answers (user_id, trait_1, trait_2, trait_3, trait_4, trait_5)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (session['user_id'], trait_1, trait_2, trait_3, trait_4, trait_5))
            conn.commit()

            cursor.execute("""
                SELECT trainer_id, tname, image_url, (
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

# 트레이너 프로필
@app.route('/trainer/<int:trainer_id>')
def trainer_profile(trainer_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
        trainer = cursor.fetchone()
    return render_template('trainer_profile.html', trainer=trainer)

# Fitpick 헬스장 정보 페이지
@app.route('/info')
def info_page():
    log_user_action()
    return render_template('info.html', user_id=session.get('user_id'))

# Fitpick 헬스장 이미지 업로드
@app.route('/image/<int:image_id>')
def get_image(image_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT image_data FROM site_images WHERE image_id = %s", (image_id,))
        row = cursor.fetchone()
        if row and row['image_data']:
            return send_file(
                io.BytesIO(row['image_data']),
                mimetype='image/jpeg'
            )
    return 'Image Not Found', 404

app.register_blueprint(profile_bp)
app.register_blueprint(edit_profile_bp)
#app.register_blueprint(mainpage_bp)
app.register_blueprint(mainpage_bp, url_prefix='/main')
app.register_blueprint(consultation_bp)

# @app.before_request
# def log_every_request():
#     # 요청 대상이 정적 파일이나 favicon.ico인 경우 제외
#     if request.path.startswith('/static/') or request.path == '/favicon.ico':
#         return
#     # 로그 기록
#     logging.info(f'{request.method} {request.path} - 요청 발생')

#     log_user_action(
#         user_id=session.get('user_id'),
#         action=f'{request.method} {request.path}',
#         target_table='',    
#         description='자동 기록된 요청'
#     )
if __name__ == '__main__':
    app.run(debug=True)
