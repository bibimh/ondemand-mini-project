from flask import Blueprint, render_template, request, abort

trainer_bp = Blueprint('trainer', __name__)

# 임시 트레이너 데이터 (목업)
mock_profiles = {
    1: {
        "name": "박철완",
        "profile_img": "trainer1.jpg",
        "intro": "운동은 습관! 함께 건강한 습관을 길러봐요.",
        "experience": "헬스 트레이너 8년 경력, IFBB 자격증 보유",
        "stats": {
            "age": {"20대": 12, "30대": 20, "40대 이상": 8},
            "gender": {"남성": 25, "여성": 15}
        }
    },
    2: {
        "name": "한나경",
        "profile_img": "trainer2.png",
        "intro": "맞춤형 루틴으로 건강한 일상 되찾기!",
        "experience": "요가 강사 5년, 필라테스 지도자 자격증 보유",
        "stats": {
            "age": {"20대": 18, "30대": 10},
            "gender": {"여성": 25, "남성": 3}
        }
    }
}

@trainer_bp.route('/profile/<int:trainer_id>', methods=['GET', 'POST'])
def profile(trainer_id):
    trainer = mock_profiles.get(trainer_id)
    if not trainer:
        abort(404)  # trainer_id가 없으면 404 페이지

    # 임시 리뷰 리스트 (나중에 DB 연동 예정)
    mock_reviews = [
        {
            "rating": 5,
            "text": "정말 친절하시고 운동도 잘 가르쳐주세요!",
            "image": "review1.jpg"
        },
        {
            "rating": 4,
            "text": "땀 많이 흘렸지만 뿌듯해요!",
            "image": None
        }
    ]

    # 리뷰 통계 계산
    review_count = len(mock_reviews)
    if review_count > 0:
        avg_rating = round(sum([r["rating"] for r in mock_reviews]) / review_count, 1)
    else:
        avg_rating = 0.0

    # 리뷰 작성 처리 (나중에 DB 연동용)
    if request.method == 'POST':
        new_rating = request.form['rating']
        new_text = request.form['review']
        # 파일 업로드는 일단 생략
        print(f"받은 리뷰: {new_rating}점 / 내용: {new_text}")
        # 나중에 DB에 저장하는 코드 작성 예정

    is_admin = True  # 로그인 연동되면 조건에 따라 설정
    return render_template(
        'profile.html', 
        trainer=trainer,
        trainer_id=trainer_id,
        reviews=mock_reviews,
        avg_rating=avg_rating,
        review_count=review_count,
        is_admin=True
    )