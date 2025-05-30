from flask import request, session
from db.db import get_db
import logging

"""클라이언트 IP 주소 추출 (프록시 지원)"""
def get_client_ip() -> str:
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr

"""사용자 행동 로그 기록"""
def log_user_action(user_id=None, action=None, target_table=None, target_id=None, description=None):
    # 로그인 안 된 경우
    if not user_id and not session.get('user_id'):
        logging.warning('[UserLog] 로그인 되지 않은 사용자 행동 기록 시도 (무시)')
        return
    # user_id가 없는 경우 세션에서 사용자 ID 가져오기
    if not user_id:
        user_id = session.get('user_id')
    
    # 자동값 처리
    action = f"{request.method} {request.path}"
    target_table = target_table or 'unknown'
    description = description or f"자동 기록된 요청: {action}"

    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO fitpick.activity_logs 
                    (user_id, activ_action, target_table, target_id, description, ip_address, user_agent) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)  
                """# , %s, %s, %s, %s, %s
                cursor.execute(sql, (
                    user_id,
                    action,
                    target_table,
                    target_id,
                    description,
                    get_client_ip(),                    # IP 추출 (프록시 대응)
                    request.user_agent.string           # User Agent 전체 문자열
                ))
                conn.commit()

                # 로그 기록
                # logging.info(log_message)
    except Exception as e:
        logging.error(f"[UserLog] Failed to log user action: {e}")
        # raise e # 예외를 다시 위로 던져야 하는 경우 사용
    # finally:
    #     if conn:
    #         conn.close()    

"""관리자 행동 로그 기록"""
def log_admin_action(admin_id=None, action=None, target_table=None, target_id=None, description=None):
    if not admin_id and not session.get('user_id'):
        logging.warning('[AdminLog] 로그인 되지 않은 사용자의 행동 기록 시도 (무시)')
        return
    if not admin_id:
        admin_id = session.get('user_id')
        
    
    # 자동값 처리
    action = f"{request.method} {request.path}" # action or f"{request.method} {request.path}"
    target_table = target_table or 'unknown'
    description = description or f"자동 기록된 요청: {action}"

    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (admin_id,))
                result = cursor.fetchone()
                is_admin = result['is_admin']
                if not result or result['is_admin'] != 1:
                    logging.warning(f"[AdminLog] 관리자 권한이 없는 사용자 user_id={admin_id}의 관리자 행동 기록 시도 (무시)")
                    return
                sql = """
                    INSERT INTO fitpick.admin_logs 
                    (admin_id, admin_action, target_table, target_id, description) 
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    admin_id,
                    action,
                    target_table,
                    target_id,
                    description
                ))
                conn.commit()
    except Exception as e:
        logging.error(f"[AdminLog] Failed to log admin action: {e}")
        # raise e
    # finally:
    #     if conn:
    #         conn.close()
