import pymysql

def get_db():
    return pymysql.connect(
        host='192.168.40.14',
        user='fitpickuser',
        password='fitpick1234',
        db='fitpick',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def insert_image(file_path, name, description):
    with open(file_path, 'rb') as f:
        image_data = f.read()

    conn = get_db()
    with conn.cursor() as cursor:
        sql = "INSERT INTO site_images (name, image_data, description) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, image_data, description))
        conn.commit()
    conn.close()

# 이미지 등록
insert_image('static/images/background.jpg', '배경', '배경 이미지')
import pymysql

def get_db():
    return pymysql.connect(
        host='192.168.40.14',
        user='fitpickuser',
        password='fitpick1234',
        db='fitpick',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def insert_image(file_path, name, description):
    with open(file_path, 'rb') as f:
        image_data = f.read()

    conn = get_db()
    with conn.cursor() as cursor:
        sql = "INSERT INTO site_images (name, image_data, description) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, image_data, description))
        conn.commit()
    conn.close()

# 이미지 등록
insert_image('static/images/background.jpg', '배경', '배경 이미지')
insert_image('static/images/trainer3_1.jpg', '트레이너3-1', '프로필 이미지')
insert_image('static/images/trainer3_2.jpg', '트레이너3-2', '프로필 이미지')
insert_image('static/images/trainer4_1.jpg', '트레이너4-1', '프로필 이미지')
insert_image('static/images/trainer5_1.jpg', '트레이너5-1', '프로필 이미지')
insert_image('static/images/trainer6_1.jpg', '트레이너6-1', '프로필 이미지')
