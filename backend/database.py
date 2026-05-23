import pymysql
from config import Config

def get_db_conn():
    # 使用 DictCursor 这样查询结果会自动转为字典，前端好处理
    return pymysql.connect(**Config.DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)