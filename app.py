from flask import Flask, render_template, request, redirect, session, jsonify, url_for, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from profile_routes import profile_bp
from profile_edit_routes import edit_profile_bp
from consultation_routes import consultation_bp
from mainpage_route import mainpage_bp
import pymysql
import io

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

# 연결 확인 코드
if __name__ == "__main__":
    try:
        conn = get_db()
        print("db 접속 성공했습니다!")
    except Exception as e:
        print(f"db 연결 실패: {e}")
    finally:
        if conn:
            conn.close()
            print("db 연결 종료")
            conn = None

# 로그인 페이지
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
    
# 회원가입
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

# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 트레이너 매칭
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

# 이미지 가져오기
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

# 블루프린트 등록
app.register_blueprint(profile_bp)
app.register_blueprint(edit_profile_bp)
app.register_blueprint(mainpage_bp)
app.register_blueprint(consultation_bp)

if __name__ == '__main__':
    app.run(debug=True)