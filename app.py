from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
from profile_routes import profile_bp
from profile_edit_routes import edit_profile_bp
from consultation_routes import consultation_bp
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

# 메인 페이지 (info.html)
@app.route('/')
def home():
    return render_template('info.html', user_id=session.get('user_id'))

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # next 파라미터로 로그인 후 리다이렉트 처리
        next_page = request.args.get('next')
        return render_template('login.html', next_page=next_page)

    login_id = request.form['login_id']
    password = request.form['password']
    next_page = request.form.get('next')

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
        
        # 관리자면 관리자 페이지로, 아니면 next 또는 메인으로
        if user['is_admin']:
            redirect_url = '/admin/consultations'
        else:
            redirect_url = next_page if next_page else '/'
            
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

# app.py에서 관리자 예약 확인 페이지 부분만 수정
#----------------------------------------------------------------------
@app.route('/admin/consultations')
def admin_consultations():
    if 'user_id' not in session or session.get('is_admin') != 1:
        return redirect('/')
    
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            print("🔍 관리자 페이지 - 데이터 조회 시작...")
            
            # 예약 목록 조회 - JOIN에서 trainer_id가 제대로 가져와지는지 확인
            cursor.execute("""
                SELECT 
                    r.reservation_id,
                    r.user_id,
                    r.trainer_id,
                    r.reservation_date,
                    r.reservation_time,
                    r.num_people,
                    r.status,
                    r.created_at,
                    t.tname as trainer_name,
                    t.image_id,
                    u.uname as user_name,
                    u.phone as user_phone
                FROM reservations r
                JOIN trainers t ON r.trainer_id = t.trainer_id
                JOIN users u ON r.user_id = u.user_id
                ORDER BY r.created_at DESC
            """)
            reservations = cursor.fetchall()
            
            print(f"📊 조회된 예약 수: {len(reservations)}개")
            
            # 첫 번째 예약의 trainer_id 확인
            if reservations:
                first_reservation = reservations[0]
                print(f"🔍 첫 번째 예약 데이터:")
                print(f"   reservation_id: {first_reservation.get('reservation_id')}")
                print(f"   trainer_id: {first_reservation.get('trainer_id')} (타입: {type(first_reservation.get('trainer_id'))})")
                print(f"   trainer_name: {first_reservation.get('trainer_name')}")
                
                # None 값 체크
                none_count = sum(1 for res in reservations if res.get('trainer_id') is None)
                if none_count > 0:
                    print(f"❌ 경고: trainer_id가 None인 예약이 {none_count}개 있습니다!")
            
            # 시간 포맷 변환 (timedelta → 문자열)
            for reservation in reservations:
                if hasattr(reservation['reservation_time'], 'total_seconds'):
                    total_seconds = int(reservation['reservation_time'].total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    reservation['reservation_time_str'] = f"{hours:02d}:{minutes:02d}"
                else:
                    reservation['reservation_time_str'] = str(reservation['reservation_time'])[:5]
            
            # 통계 정보
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
            
            # 트레이너 목록
            cursor.execute("SELECT trainer_id, tname FROM trainers WHERE is_hidden = 0")
            trainers = cursor.fetchall()
            
            print(f"📊 통계:")
            print(f"   전체 예약: {total_count}")
            print(f"   오늘 예약: {today_count}")
            print(f"   이번달 예약: {month_count}")
            print(f"   활성 트레이너: {active_trainers}")
            print(f"   트레이너 목록: {len(trainers)}명")
        
        return render_template('admin_consultations.html',
                             reservations=reservations,
                             total_count=total_count,
                             today_count=today_count,
                             month_count=month_count,
                             active_trainers=active_trainers,
                             trainers=trainers)
    
    except Exception as e:
        print(f"❌ 관리자 페이지 오류: {e}")
        import traceback
        traceback.print_exc()
        return f"예약 목록을 불러올 수 없습니다.<br>오류: {e}", 500
    
    finally:
        conn.close()
#------------------------------------------------------------------------여기까지

# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 트레이너 매칭
@app.route('/match', methods=['GET', 'POST'])
def match_trainer():
    if request.method == 'POST':
        trait_1 = request.form['trait_1']
        trait_2 = request.form['trait_2']
        trait_3 = request.form['trait_3']
        trait_4 = request.form['trait_4']
        trait_5 = request.form['trait_5']

        conn = get_db()
        with conn.cursor() as cursor:
            # 로그인한 사용자라면 답변 저장
            if 'user_id' in session:
                cursor.execute("""
                    INSERT INTO user_answers (user_id, trait_1, trait_2, trait_3, trait_4, trait_5)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (session['user_id'], trait_1, trait_2, trait_3, trait_4, trait_5))
                conn.commit()

            # 매칭 점수 계산
            cursor.execute("""
                SELECT trainer_id, tname, image_id, (
                    (trait_1 = %s) + (trait_2 = %s) + (trait_3 = %s) +
                    (trait_4 = %s) + (trait_5 = %s)
                ) AS match_score
                FROM trainers
                WHERE is_hidden = 0
                ORDER BY match_score DESC
                LIMIT 1
            """, (trait_1, trait_2, trait_3, trait_4, trait_5))
            best_match = cursor.fetchone()

        return render_template('match_result.html', trainer=best_match)
    
    return render_template('match_form.html')

# 트레이너 프로필 (개별)
@app.route('/trainer/<int:trainer_id>')
def trainer_profile(trainer_id):
    conn = get_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
        trainer = cursor.fetchone()
    return render_template('trainer_profile.html', trainer=trainer)

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
                mimetype=row['mimetype'] or 'application/octet-stream'
            )
    return 'Image Not Found', 404

# 블루프린트 등록
app.register_blueprint(profile_bp)
app.register_blueprint(edit_profile_bp)
app.register_blueprint(consultation_bp)

if __name__ == '__main__':
    app.run(debug=True)