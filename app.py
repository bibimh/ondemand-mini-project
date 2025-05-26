from flask import Flask, render_template
from routes.profile_routes import trainer_bp

app = Flask(__name__)

# Blueprint 등록
app.register_blueprint(trainer_bp)

# 테스트
@app.route('/')
def index():
    return render_template('index.html')  # templates/index.html 불러오기

if __name__ == '__main__':
    app.run(debug=True)
