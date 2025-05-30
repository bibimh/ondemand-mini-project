```MERGE_FITPICK/
├── app.py # 플라스크 메인 실행 파일
├── requirements.txt # 의존성 리스트
├── .gitignore # Git 무시 파일 목록
│
├── db/ # 초기 데이터 및 DB 관련 파일
│ ├── consultation_init.sql
│ ├── db.py
│ └── pycache/
│
├── models/ # DB 모델 정의
│ └── consultation.py
│
├── static/ # 정적 파일
│ ├── css/
│ │ ├── background.css
│ │ ├── basic.css
│ │ ├── consultation.css
│ │ ├── edit_profile.css
│ │ ├── info.css
│ │ ├── login.css
│ │ ├── main_background.css
│ │ └── profile.css
│ │
│ ├── images/
│ │ ├── background.jpg
│ │ ├── trainer3_1.jpg
│ │ ├── trainer3_2.jpg
│ │ ├── trainer4_1.jpg
│ │ ├── trainer5_1.jpg
│ │ ├── trainer5_2.jpg
│ │ └── trainer6_1.jpg
│ │
│ └── js/
│ ├── consultation.js
│ ├── login.js
│ └── validation.js
│
├── templates/ # HTML 템플릿
│ ├── admin_consultations.html
│ ├── base.html
│ ├── consultation.html
│ ├── edit_profile.html
│ ├── info.html
│ ├── login.html
│ ├── mainpage.html
│ ├── match_form.html
│ ├── match_result.html
│ ├── profile.html
│ └── partials/
│ └── review_list.html
│
├── venv/ # 가상 환경 (보통 .gitignore 처리)
│
├── consultation_routes.py # 상담 관련 라우트
├── init_images.py # 이미지 초기화 관련 스크립트
├── mainpage_route.py # 메인페이지 라우트
├── profile_edit_routes.py # 프로필 수정 라우트
└── profile_routes.py # 프로필 관련 라우트```
