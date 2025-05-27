# db.py

import pymysql

conn = pymysql.connect(
    host='localhost',
    user='yunha',
    password='admin',
    db='fitpick_test',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)