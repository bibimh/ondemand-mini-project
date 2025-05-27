# 상담 신청 기능 (김철환)

## 구현 기능
- 트레이너 상담 신청
- 날짜/시간 선택
- 예약 조회 및 취소

## 라우트
- `/consultation/<trainer_id>` - 상담 신청 페이지
- `/api/consultation` - 상담 신청 API
- `/my-reservations` - 내 예약 목록

## 필요한 세션 정보
- `session['user_id']` - 사용자 ID
- `session['user_name']` - 사용자 이름
- `session['user_phone']` - 전화번호

## 사용 라이브러리
- Flatpickr (날짜 선택)