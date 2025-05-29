from flask import Blueprint, render_template

mainpage_bp = Blueprint('mainpage', __name__)

# 메인페이지 라우팅
@mainpage_bp.route('/')
def mainpage():
    return render_template('mainpage.html')  # 메인페이지 열기

# 각 메뉴 버튼별 라우트
@mainpage_bp.route('/center')
def center():
    return "<h1>센터 페이지</h1>"

@mainpage_bp.route('/login')
def login():
    return "<h1>로그인 페이지</h1>"

@mainpage_bp.route('/fitpick')
def fitpick():
    return "<h1>Fit Pick 페이지</h1>"

# 트레이너 박스 클릭 시 연결될 예시 페이지들
@mainpage_bp.route('/tpage1')
def tpage1():
    return "<h1>Fit Pick 페이지</h1>"

@mainpage_bp.route('/tpage2')
def tpage2():
    return "<h1>트레이너2 상세페이지</h1>"

@mainpage_bp.route('/tpage3')
def tpage3():
    return "<h1>트레이너3 상세페이지</h1>"

@mainpage_bp.route('/tpage4')
def tpage4():
    return "<h1>Fit Pick 페이지</h1>"

@mainpage_bp.route('/tpage5')
def tpage5():
    return "<h1>Fit Pick 페이지</h1>"

@mainpage_bp.route('/tpage6')
def tpage6():
    return "<h1>Fit Pick 페이지</h1>"

@mainpage_bp.route('/tpage7')
def tpage7():
    return "<h1>트레이너7 상세페이지</h1>"

@mainpage_bp.route('/tpage8')
def tpage8():
    return "<h1>Fit Pick 페이지</h1>"

@mainpage_bp.route('/tpage9')
def tpage9():
    return "<h1>트레이너9 상세페이지</h1>"

@mainpage_bp.route('/tpage10')
def tpage10():
    return "<h1>Fit Pick 페이지</h1>"