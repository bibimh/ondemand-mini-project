from datetime import datetime

class Consultation:
    def __init__(self, db):
        self.db = db
        self.create_table()
    
    def create_table(self):
        """상담 예약 테이블 생성"""
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trainer_id INTEGER NOT NULL,
                consultation_datetime TEXT NOT NULL,
                num_people INTEGER DEFAULT 1,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                content TEXT,
                status TEXT DEFAULT 'pending',  -- pending, confirmed, completed, cancelled
                created_at TEXT NOT NULL,
                confirmed_at TEXT,
                cancelled_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (trainer_id) REFERENCES trainers(id)
            )
        ''')
        self.db.commit()
    
    def create_consultation(self, user_id, trainer_id, consultation_datetime, 
                          num_people, name, phone, content=''):
        """새로운 상담 예약 생성"""
        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO consultations 
            (user_id, trainer_id, consultation_datetime, num_people, 
             name, phone, content, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (
            user_id, trainer_id, consultation_datetime, num_people,
            name, phone, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        self.db.commit()
        return cursor.lastrowid
    
    def get_consultations_by_user(self, user_id):
        """사용자의 모든 상담 예약 조회"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT c.*, t.name as trainer_name, t.specialty
            FROM consultations c
            JOIN trainers t ON c.trainer_id = t.id
            WHERE c.user_id = ?
            ORDER BY c.consultation_datetime DESC
        ''', (user_id,))
        return cursor.fetchall()
    
    def get_consultations_by_trainer(self, trainer_id, date=None):
        """트레이너의 상담 예약 조회"""
        cursor = self.db.cursor()
        if date:
            cursor.execute('''
                SELECT c.*, u.name as user_name
                FROM consultations c
                JOIN users u ON c.user_id = u.id
                WHERE c.trainer_id = ? 
                AND DATE(c.consultation_datetime) = ?
                AND c.status != 'cancelled'
                ORDER BY c.consultation_datetime
            ''', (trainer_id, date))
        else:
            cursor.execute('''
                SELECT c.*, u.name as user_name
                FROM consultations c
                JOIN users u ON c.user_id = u.id
                WHERE c.trainer_id = ?
                ORDER BY c.consultation_datetime DESC
            ''', (trainer_id,))
        return cursor.fetchall()
    
    def get_consultation_by_id(self, consultation_id):
        """특정 상담 예약 조회"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT c.*, t.name as trainer_name, u.name as user_name
            FROM consultations c
            JOIN trainers t ON c.trainer_id = t.id
            JOIN users u ON c.user_id = u.id
            WHERE c.id = ?
        ''', (consultation_id,))
        return cursor.fetchone()
    
    def update_consultation_status(self, consultation_id, status):
        """상담 예약 상태 업데이트"""
        cursor = self.db.cursor()
        timestamp_field = None
        timestamp_value = None
        
        if status == 'confirmed':
            timestamp_field = 'confirmed_at'
            timestamp_value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elif status == 'cancelled':
            timestamp_field = 'cancelled_at'
            timestamp_value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if timestamp_field:
            cursor.execute(f'''
                UPDATE consultations 
                SET status = ?, {timestamp_field} = ?
                WHERE id = ?
            ''', (status, timestamp_value, consultation_id))
        else:
            cursor.execute('''
                UPDATE consultations 
                SET status = ?
                WHERE id = ?
            ''', (status, consultation_id))
        
        self.db.commit()
    
    def cancel_consultation(self, consultation_id, user_id):
        """상담 예약 취소"""
        cursor = self.db.cursor()
        
        # 본인 예약인지 확인
        cursor.execute('''
            SELECT user_id FROM consultations WHERE id = ?
        ''', (consultation_id,))
        result = cursor.fetchone()
        
        if result and result[0] == user_id:
            self.update_consultation_status(consultation_id, 'cancelled')
            return True
        return False
    
    def get_available_times(self, trainer_id, date):
        """특정 날짜의 예약 가능한 시간 조회"""
        cursor = self.db.cursor()
        cursor.execute('''
            SELECT TIME(consultation_datetime) as time
            FROM consultations
            WHERE trainer_id = ?
            AND DATE(consultation_datetime) = ?
            AND status != 'cancelled'
        ''', (trainer_id, date))
        
        booked_times = [row[0] for row in cursor.fetchall()]
        
        # 운영 시간 (9시~21시)
        all_times = [f"{hour:02d}:00" for hour in range(9, 22)]
        
        # 예약 가능한 시간 = 전체 시간 - 예약된 시간
        available_times = [time for time in all_times if time not in booked_times]
        
        return {
            'all_times': all_times,
            'booked_times': booked_times,
            'available_times': available_times
        }
    
    def get_consultation_stats(self, trainer_id):
        """트레이너의 상담 통계"""
        cursor = self.db.cursor()
        
        # 전체 상담 수
        cursor.execute('''
            SELECT COUNT(*) FROM consultations
            WHERE trainer_id = ? AND status = 'completed'
        ''', (trainer_id,))
        total_consultations = cursor.fetchone()[0]
        
        # 이번 달 상담 수
        cursor.execute('''
            SELECT COUNT(*) FROM consultations
            WHERE trainer_id = ? 
            AND status = 'completed'
            AND strftime('%Y-%m', consultation_datetime) = strftime('%Y-%m', 'now')
        ''', (trainer_id,))
        monthly_consultations = cursor.fetchone()[0]
        
        # 취소율
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled,
                COUNT(*) as total
            FROM consultations
            WHERE trainer_id = ?
        ''', (trainer_id,))
        result = cursor.fetchone()
        cancel_rate = (result[0] / result[1] * 100) if result[1] > 0 else 0
        
        return {
            'total_consultations': total_consultations,
            'monthly_consultations': monthly_consultations,
            'cancel_rate': round(cancel_rate, 1)
        }