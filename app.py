# app.py

from flask import Flask, render_template
from routes.profile_routes import profile_bp
from routes.profile_edit_routes import edit_profile_bp

app = Flask(__name__)

# Blueprint 등록
app.register_blueprint(profile_bp)
app.register_blueprint(edit_profile_bp)

# 테스트
@app.route('/')
def index():
    return render_template('index.html')  # templates/index.html 불러오기

if __name__ == '__main__':
    app.run(debug=True)
