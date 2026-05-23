import pymysql

class Config:
    # 基础配置
    DEBUG = True
    PORT = 5002
    HOST = '0.0.0.0'
    
    # MySQL 数据库配置
    MYSQL_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '060821', # 记得改成 060821
        'database': 'rag',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    # 可以在这里扩展其他配置，比如 LLM 的 API KEY 等
    # LLM_MODEL_PATH = "/path/to/your/model"