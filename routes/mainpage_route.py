from flask import Blueprint, redirect, render_template
from db.db import get_all_trainers  

mainpage_bp = Blueprint('mainpage', __name__)

@mainpage_bp.route('/')
def mainpage():
    # 트레이너 데이터 가져오기 (최대 9개)
    trainers = get_all_trainers()
    
    # 트레이너 데이터가 9개 미만인 경우를 대비하여 빈 슬롯 처리는 템플릿에서
    return render_template('mainpage.html', trainers=trainers)

@mainpage_bp.route('/center')
def center():
    return "<h1>센터 페이지</h1>"

@mainpage_bp.route('/login')
def login():
    return "<h1>로그인 페이지</h1>"

@mainpage_bp.route('/fitpick')
def fitpick():
    return "<h1>Fit Pick 페이지</h1>"

@mainpage_bp.route('/tpage<int:trainer_id>')
def trainer_detail_redirect(trainer_id):
    return redirect(f'/profile/{trainer_id}')