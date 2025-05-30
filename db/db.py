import pymysql
from contextlib import contextmanager

# DB 연결 설정
DB_CONFIG = {
    'host': '',
    'user': '',
    'password': '',
    'db': '',
    'charset': '',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """데이터베이스 연결을 반환하는 함수"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("db 접속 성공했습니다!")
        return conn
    except Exception as e:
        print(f"db 연결 실패: {e}")
        return None

@contextmanager
def get_db():
    """컨텍스트 매니저로 DB 연결 관리"""
    conn = None
    try:
        conn = get_db_connection()
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"DB 오류: {e}")
        raise
    finally:
        if conn:
            conn.close()

# 트레이너 관련 함수들 개선
def get_all_trainers():
    """모든 활성화된 트레이너 목록 조회 (메인페이지용, 최대 9개)"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT trainer_id, tname, 
                       COALESCE(
                           (SELECT image_id FROM site_images 
                            WHERE name LIKE CONCAT('trainer', trainer_id, '_%') 
                            ORDER BY uploaded_at ASC LIMIT 1), 
                           48
                       ) as image_id
                FROM trainers 
                WHERE is_hidden = 0 
                ORDER BY trainer_id
                LIMIT 9
            """)
            result = cursor.fetchall()
            
            # image_id가 NULL일 경우 기본값 48로 대체
            for row in result:
                if row['image_id'] is None:
                    row['image_id'] = 48
                    
            return result

def get_trainer_by_id(trainer_id):
    """특정 트레이너 정보 조회 (숨김 처리 여부 상관없이)"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM trainers WHERE trainer_id = %s", (trainer_id,))
            return cursor.fetchone()

def get_active_trainer_by_id(trainer_id):
    """특정 활성화된 트레이너 정보 조회 (is_hidden = 0만)"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM trainers 
                WHERE trainer_id = %s AND is_hidden = 0
            """, (trainer_id,))
            return cursor.fetchone()

# 예약 관련 함수들
def get_reserved_times(trainer_id, date):
    """특정 트레이너의 특정 날짜 예약된 시간 조회"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT reservation_time 
                FROM reservations 
                WHERE trainer_id = %s AND reservation_date = %s AND status != 2
            """, (trainer_id, date))
            return [row['reservation_time'] for row in cursor.fetchall()]

def create_reservation(user_id, trainer_id, date, time, num_people):
    """예약 생성"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reservations (user_id, trainer_id, reservation_date, reservation_time, num_people)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, trainer_id, date, time, num_people))
            conn.commit()
            return cursor.lastrowid

# 사용자 관련 함수들
def get_user_by_login_id(login_id):
    """로그인 ID로 사용자 조회"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE login_id = %s", (login_id,))
            return cursor.fetchone()

def create_user(login_id, password_hash, uname, phone, gender, birthday):
    """새 사용자 생성"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (login_id, password_hash, uname, phone, gender, birthday)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (login_id, password_hash, uname, phone, gender, birthday))
            conn.commit()
            return cursor.lastrowid

# 리뷰 관련 함수들
def get_trainer_reviews(trainer_id):
    """트레이너 리뷰 조회"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT r.*, u.uname 
                FROM reviews r 
                JOIN users u ON r.user_id = u.user_id 
                WHERE r.trainer_id = %s 
                ORDER BY r.created_at DESC
            """, (trainer_id,))
            return cursor.fetchall()

def get_trainer_avg_rating(trainer_id):
    """트레이너 평균 평점 조회"""
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT AVG(rating) as avg_rating, COUNT(*) as review_count 
                FROM reviews 
                WHERE trainer_id = %s
            """, (trainer_id,))
            result = cursor.fetchone()
            return {
                'avg_rating': round(result['avg_rating'], 1) if result['avg_rating'] else 0,
                'review_count': result['review_count']
            }# db.py
