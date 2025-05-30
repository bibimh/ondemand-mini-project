import os
import logging
from logging.handlers import RotatingFileHandler

"""로깅 설정 초기화"""
def setup_logging():
    # 로그 디렉토리 없으면 새로 생성
    if not os.path.exists('logs'):
        os.makedirs('logs') 

    log_file = 'logs/fitpick.log'

    # 파일 크기 기준 회전 로그 핸들러 설정 (1MB, 백업 5개 유지)
    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5, encoding='utf-8')
    handler.setLevel(logging.WARNING)

    # 로그 출력 포맷 설정
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # 기본 로거에 핸들러 추가 및 로그 레벨 설정
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)
    if not logger.handlers:
        logger.addHandler(handler)