from flask import Flask
from routes.mainpage_route import mainpage_bp  # mainpage의 Blueprint를 불러옴

app = Flask(__name__)
app.register_blueprint(mainpage_bp)  # Blueprint 등록

if __name__ == '__main__':
    app.run(debug=True)  # 서버 실행
