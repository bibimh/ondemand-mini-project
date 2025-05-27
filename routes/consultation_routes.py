from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import sqlite3

consultation_bp = Blueprint('consultation', __name__)

# 상담 신청 페이지
@consultation_bp.route('/consultation/<int:trainer_id>')
def consultation(trainer_id):
    # 로그인 확인
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.url))
    
    # 트레이너 정보 가져오기
    conn = sqlite3.connect('fitpick.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, specialty, profile_image 
        FROM trainers 
        WHERE id = ?
    ''', (trainer_id,))
    
    trainer = cursor.fetchone()
    conn.close()
    
    if not trainer:
        return "트레이너를 찾을 수 없습니다.", 404
    
    trainer_data = {
        'id': trainer[0],
        'name': trainer[1],
        'specialty': trainer[2],
        'profile_image': trainer[3] or '/static/images/default-trainer.png'
    }
    
    return render_template('consultation.html', trainer=trainer_data)

# 상담 신청 처리
@consultation_bp.route('/api/consultation', methods=['POST'])
def submit_consultation():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    try:
        # 폼 데이터 받기
        trainer_id = request.form.get('trainer_id')
        consultation_date = request.form.get('consultation_date')
        consultation_time = request.form.get('consultation_time')
        num_people = request.form.get('num_people')
        name = request.form.get('name')
        phone = request.form.get('phone')
        consultation_content = request.form.get('consultation_content', '')
        
        # 날짜/시간 결합
        consultation_datetime = f"{consultation_date} {consultation_time}"
        
        # DB에 저장
        conn = sqlite3.connect('fitpick.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO consultations 
            (user_id, trainer_id, consultation_datetime, num_people, 
            name, phone, content, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
        ''', (
            session['user_id'],
            trainer_id,
            consultation_datetime,
            num_people,
            name,
            phone,
            consultation_content,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        conn.close()
        
        # 실제로는 SMS 발송 등의 알림 처리
        # send_sms_notification(phone, consultation_datetime)
        
        return jsonify({'success': True, 'message': '상담 신청이 완료되었습니다.'})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': '상담 신청 중 오류가 발생했습니다.'}), 500

# 예약 가능한 시간 조회
@consultation_bp.route('/api/available-times/<int:trainer_id>/<date>')
def get_available_times(trainer_id, date):
    try:
        # 해당 날짜의 예약된 시간 조회
        conn = sqlite3.connect('fitpick.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT consultation_datetime 
            FROM consultations 
            WHERE trainer_id = ? 
            AND DATE(consultation_datetime) = ?
            AND status != 'cancelled'
        ''', (trainer_id, date))
        
        booked_times = [row[0].split(' ')[1] for row in cursor.fetchall()]
        conn.close()
        
        # 전체 가능한 시간대
        all_times = [
            '09:00', '10:00', '11:00', '12:00',
            '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00'
        ]
        
        # 예약 가능한 시간만 필터링
        available_times = [time for time in all_times if time not in booked_times]
        
        return jsonify({
            'success': True,
            'available_times': available_times,
            'booked_times': booked_times
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': '시간 조회 중 오류가 발생했습니다.'}), 500

# 내 상담 예약 조회
@consultation_bp.route('/my-consultations')
def my_consultations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('fitpick.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, t.name as trainer_name
        FROM consultations c
        JOIN trainers t ON c.trainer_id = t.id
        WHERE c.user_id = ?
        ORDER BY c.consultation_datetime DESC
    ''', (session['user_id'],))
    
    consultations = cursor.fetchall()
    conn.close()
    
    return render_template('my_consultations.html', consultations=consultations)

# 상담 취소
@consultation_bp.route('/api/consultation/<int:consultation_id>/cancel', methods=['POST'])
def cancel_consultation(consultation_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '로그인이 필요합니다.'}), 401
    
    try:
        conn = sqlite3.connect('fitpick.db')
        cursor = conn.cursor()
        
        # 본인 예약인지 확인
        cursor.execute('''
            SELECT user_id, consultation_datetime 
            FROM consultations 
            WHERE id = ?
        ''', (consultation_id,))
        
        result = cursor.fetchone()
        if not result or result[0] != session['user_id']:
            return jsonify({'success': False, 'message': '권한이 없습니다.'}), 403
        
        # 24시간 이전인지 확인
        consultation_time = datetime.strptime(result[1], '%Y-%m-%d %H:%M')
        if consultation_time - datetime.now() < timedelta(hours=24):
            return jsonify({'success': False, 'message': '상담 24시간 전에는 취소가 불가능합니다.'}), 400
        
        # 상태 업데이트
        cursor.execute('''
            UPDATE consultations 
            SET status = 'cancelled', 
                cancelled_at = ?
            WHERE id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), consultation_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '상담이 취소되었습니다.'})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': '취소 중 오류가 발생했습니다.'}), 500