# routes/consultation_routes.py - 김철환 담당 상담 신청 시스템
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.db import get_trainer_by_id, get_active_trainer_by_id, get_reserved_times, create_reservation

consultation_bp = Blueprint('consultation', __name__)

@consultation_bp.route('/consultation/<int:trainer_id>')
def consultation_page(trainer_id):
    """상담 페이지 - 트레이너 프로필에서 상담신청하기 버튼 클릭시"""
    # 로그인 확인 - 로그인 안했으면 로그인 페이지로
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    # 활성화된 트레이너만 조회 (is_hidden = 0)
    trainer = get_active_trainer_by_id(trainer_id)
    if not trainer:
        return "해당 트레이너를 찾을 수 없거나 현재 상담 신청을 받지 않고 있습니다.", 404
    
    # 오늘 날짜와 최대 예약 가능 날짜 (30일 후)
    today = datetime.now().strftime('%Y-%m-%d')
    max_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    # 템플릿 파일명을 consultation.html로 변경
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

@consultation_bp.route('/admin/consultations')
def admin_consultations():
    """관리자 전용 - 상담 예약 목록 보기"""
    # 관리자 권한 확인
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('auth.login'))
    
    try:
        from db.db import get_db
        
        print("🔍 관리자 페이지 접속 시도...")
        
        with get_db() as conn:
            with conn.cursor() as cursor:
                print("✅ DB 연결 성공")
                
                # 단계별 디버깅
                print("📊 통계 정보 조회 중...")
                
                # 1. 기본 통계
                cursor.execute("SELECT COUNT(*) as total FROM reservations")
                total_count = cursor.fetchone()['total']
                print(f"   전체 예약: {total_count}건")
                
                cursor.execute("SELECT COUNT(*) as active FROM trainers WHERE is_hidden = 0")
                active_trainers = cursor.fetchone()['active']
                print(f"   활성 트레이너: {active_trainers}명")
                
                # 2. 오늘/이번달 통계 (안전한 방식으로)
                cursor.execute("SELECT COUNT(*) as today FROM reservations WHERE reservation_date = CURDATE()")
                today_count = cursor.fetchone()['today']
                print(f"   오늘 예약: {today_count}건")
                
                cursor.execute("""
                    SELECT COUNT(*) as month 
                    FROM reservations 
                    WHERE reservation_date >= DATE_FORMAT(NOW(), '%Y-%m-01')
                """)
                month_count = cursor.fetchone()['month']
                print(f"   이번달 예약: {month_count}건")
                
                # 3. 트레이너 목록
                print("🏋️‍♂️ 트레이너 목록 조회 중...")
                cursor.execute("SELECT trainer_id, tname FROM trainers WHERE is_hidden = 0")
                trainers = cursor.fetchall()
                print(f"   조회된 트레이너: {len(trainers)}명")
                
                # 4. 예약 목록 조회 (단순화)
                print("📅 예약 목록 조회 중...")
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
                        t.tname,
                        t.image_url,
                        u.uname,
                        u.phone
                    FROM reservations r
                    JOIN trainers t ON r.trainer_id = t.trainer_id
                    JOIN users u ON r.user_id = u.user_id
                    ORDER BY r.created_at DESC
                """)
                reservations = cursor.fetchall()
                print(f"   조회된 예약: {len(reservations)}건")
                
                # 시간 포맷 변환 (timedelta → 문자열)
                for reservation in reservations:
                    if isinstance(reservation['reservation_time'], type(reservation['reservation_time'])):
                        # timedelta를 HH:MM 형식으로 변환
                        total_seconds = int(reservation['reservation_time'].total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        reservation['reservation_time_str'] = f"{hours:02d}:{minutes:02d}"
                    else:
                        reservation['reservation_time_str'] = str(reservation['reservation_time'])
                
                # 각 예약 정보 출력 (디버깅용)
                for i, res in enumerate(reservations[:3]):  # 처음 3개만
                    print(f"   예약 {i+1}: #{res['reservation_id']} - {res['tname']} - {res['uname']} - {res.get('reservation_time_str', 'N/A')}")
        
        print("🎉 모든 데이터 조회 완료, 템플릿 렌더링 중...")
        
        return render_template('admin_consultations.html',
                             reservations=reservations,
                             total_count=total_count,
                             today_count=today_count,
                             month_count=month_count,
                             active_trainers=active_trainers,
                             trainers=trainers)
        
    except Exception as e:
        print(f"❌ 상세 오류 정보:")
        print(f"   오류 메시지: {e}")
        print(f"   오류 타입: {type(e)}")
        
        # 스택 트레이스 출력
        import traceback
        traceback.print_exc()
        
        return f"예약 목록을 불러올 수 없습니다.<br>오류: {e}", 500