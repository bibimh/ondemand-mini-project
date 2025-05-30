import pymysql
from mimetypes import guess_type

def get_db():
    return pymysql.connect(
        host='',
        user='',
        password='',
        db='',
        charset='',
        cursorclass=pymysql.cursors.DictCursor
    )

def insert_image(file_path, name, description):
    with open(file_path, 'rb') as f:
        image_data = f.read()

    # 파일 확장자 기반으로 MIME 타입 추정
    mimetype, _ = guess_type(file_path)
    if mimetype is None:
        mimetype = 'application/octet-stream'  # 추정 실패 시 기본값

    conn = get_db()
    with conn.cursor() as cursor:
        sql = "INSERT INTO site_images (name, image_data, mimetype, description) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (name, image_data, mimetype, description))
        conn.commit()
    conn.close()
 
# 이미지 등록 
insert_image('static/images/default.jpg', '기본', '기본 이미지')
