from flask import Blueprint, redirect, render_template
from db.db import get_all_trainers  

mainpage_bp = Blueprint('mainpage', __name__)

@mainpage_bp.route('/')
def mainpage():
    trainers = get_all_trainers()
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