# ondemand-mini-project

# FitPick
퍼스널 트레이너 추천 플랫폼입니다.

## 실행 방법
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## 기본 구조
```plaintext
fitpick/
├── app.py                     # 플라스크 메인 실행 파일
├── requirements.txt           # 의존성 리스트
├── .gitignore                 # 무시할 파일 목록
├── README.md                  # 프로젝트 소개
│
├── templates/                 # HTML 파일
│   ├── index.html
│   ├── trainer_profile.html
│
├── static/                    # 정적 파일 (CSS, JS, 이미지 등)
│   ├── css/
│   ├── js/
│   └── images/
│
├── routes/                    # Flask 라우트 분리
│   └── trainer_routes.py
│
├── models/                    # DB 모델 정의
│   └── trainer.py
│
├── db/                        # 초기 데이터나 SQL 파일
│   └── init.sql
```
