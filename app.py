from flask import Flask, render_template

app = Flask(__name__)

# 테스트
@app.route('/')
def index():
    return render_template('index.html')  # templates/index.html 불러오기

if __name__ == '__main__':
    app.run(debug=True)
