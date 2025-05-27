# routes/consultation_routes.py - 김철환 담당 상담 신청 시스템
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db import get_trainer_by_id, get_reserved_times, create_reservation

consultation_bp = Blueprint('consultation', __name__)

@consultation_bp.route('/consultation/<int:trainer_id>')
def consultation_page(trainer_id):
    """상담 페이지 - 트레이너 프로필에서 상담신청하기 버튼 클릭시"""
    # 로그인 확인 - 로그인 안했으면 로그인 페이지로
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    trainer = get_trainer_by_id(trainer_id)
    if not trainer:
        return "트레이너를 찾을 수 없습니다.", 404
    
    # 오늘 날짜와 최대 예약 가능 날짜 (30일 후)
    today = datetime.now().strftime('%Y-%m-%d')
    max_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    return render_template('consultation.html', 
                         trainer=trainer, 
                         today=today, 
                         max_date=max_date)

@consultation_bp.route('/api/reserved-times/<int:trainer_id>/<date>')
def get_reserved_times_api(trainer_id, date):
    """특정 날짜의 예약된 시간 조회 API - 선택된 시간 다른사람이 선택불가하게"""
    try:
        reserved_times = get_reserved_times(trainer_id, date)
        # 시간을 문자열로 변환 (HH:MM 형식)
        reserved_times_str = [str(time)[:5] for time in reserved_times]
        return jsonify({
            'success': True,
            'reserved_times': reserved_times_str
        })
    except Exception as e:
        print(f"예약된 시간 조회 오류: {e}")
        return jsonify({
            'success': False,
            'message': '예약된 시간을 조회할 수 없습니다.'
        }), 500

@consultation_bp.route('/api/create-consultation', methods=['POST'])
def create_consultation_api():
    """상담 신청 생성 API - 최종 상담 신청 확정"""
    # 로그인 확인
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': '로그인이 필요합니다.'
        }), 401
    
    try:
        data = request.get_json()
        user_id = session['user_id']
        trainer_id = data.get('trainer_id')
        consultation_date = data.get('consultation_date')
        consultation_time = data.get('consultation_time')
        num_people = data.get('num_people', 1)
        
        # 입력값 검증
        if not all([trainer_id, consultation_date, consultation_time]):
            return jsonify({
                'success': False,
                'message': '필수 정보가 누락되었습니다.'
            }), 400
        
        # 날짜 형식 검증
        try:
            datetime.strptime(consultation_date, '%Y-%m-%d')
            datetime.strptime(consultation_time, '%H:%M')
        except ValueError:
            return jsonify({
                'success': False,
                'message': '날짜 또는 시간 형식이 올바르지 않습니다.'
            }), 400
        
        # 과거 날짜 예약 방지
        consultation_datetime = datetime.strptime(f"{consultation_date} {consultation_time}", '%Y-%m-%d %H:%M')
        if consultation_datetime <= datetime.now():
            return jsonify({
                'success': False,
                'message': '과거 시간으로는 신청할 수 없습니다.'
            }), 400
        
        # 이미 예약된 시간인지 재확인 (동시 예약 방지)
        reserved_times = get_reserved_times(trainer_id, consultation_date)
        reserved_times_str = [str(time)[:5] for time in reserved_times]
        if consultation_time in reserved_times_str:
            return jsonify({
                'success': False,
                'message': '이미 예약된 시간입니다. 다른 시간을 선택해주세요.'
            }), 400
        
        # 상담 신청 생성
        consultation_id = create_reservation(
            user_id=user_id,
            trainer_id=trainer_id,
            date=consultation_date,
            time=consultation_time,
            num_people=num_people
        )
        
        return jsonify({
            'success': True,
            'message': '상담 신청이 완료되었습니다.',
            'consultation_id': consultation_id
        })
        
    except Exception as e:
        print(f"상담 신청 생성 오류: {e}")
        return jsonify({
            'success': False,
            'message': '상담 신청 중 오류가 발생했습니다.'
        }), 500

@consultation_bp.route('/my-consultations')
def my_consultations():
    """내 상담 신청 목록 조회"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    try:
        from db.db import get_db
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT r.*, t.tname, t.image_url
                    FROM reservations r
                    JOIN trainers t ON r.trainer_id = t.trainer_id
                    WHERE r.user_id = %s
                    ORDER BY r.reservation_date DESC, r.reservation_time DESC
                """, (session['user_id'],))
                consultations = cursor.fetchall()
        
        return render_template('my_consultations.html', consultations=consultations)
        
    except Exception as e:
        print(f"내 상담 목록 조회 오류: {e}")
        return "상담 목록을 불러올 수 없습니다.", 500

@consultation_bp.route('/cancel-consultation/<int:consultation_id>', methods=['POST'])
def cancel_consultation(consultation_id):
    """상담 신청 취소"""
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': '로그인이 필요합니다.'
        }), 401
    
    try:
        from db.db import get_db
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                # 본인의 상담 신청인지 확인
                cursor.execute("""
                    SELECT * FROM reservations 
                    WHERE reservation_id = %s AND user_id = %s AND status != 2
                """, (consultation_id, session['user_id']))
                
                consultation = cursor.fetchone()
                if not consultation:
                    return jsonify({
                        'success': False,
                        'message': '상담 신청을 찾을 수 없습니다.'
                    }), 404
                
                # 상담 신청 취소 (status = 2)
                cursor.execute("""
                    UPDATE reservations 
                    SET status = 2 
                    WHERE reservation_id = %s
                """, (consultation_id,))
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'message': '상담 신청이 취소되었습니다.'
                })
                
    except Exception as e:
        print(f"상담 신청 취소 오류: {e}")
        return jsonify({
            'success': False,
            'message': '상담 신청 취소 중 오류가 발생했습니다.'
        }), 500