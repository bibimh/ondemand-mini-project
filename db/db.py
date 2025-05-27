# db.py

import pymysql

conn = pymysql.connect(
    host='192.168.40.14',
    user='fitpickuser',
    password='fitpick1234',
    db='fitpick',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)