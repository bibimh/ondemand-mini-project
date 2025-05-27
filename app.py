from flask import Flask, render_template
from routes.consultation_routes import consultation_bp

app = Flask(__name__)
app.register_blueprint(consultation_bp)

# 테스트
@app.route('/')
def index():
    return render_template('index.html')  # templates/index.html 불러오기

if __name__ == '__main__':
    app.run(debug=True)
