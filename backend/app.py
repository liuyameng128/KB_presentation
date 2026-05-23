from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
from config import Config

# 导入你的模块
from modules.auth import auth_bp
from modules.chat import chat_bp
from modules.knowledge import knowledge_bp  # 取消注释

app = Flask(__name__)
# 允许前端跨域访问，允许 credentials
CORS(app, origins=['http://localhost:5173', 'http://127.0.0.1:5173'], supports_credentials=True)

# 数据库连接函数，从 Config 中读取参数
def get_db_connection():
    return pymysql.connect(**Config.MYSQL_CONFIG)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    # 映射前端角色到数据库 ENUM 类型
    mapped_role = 'operator' if role == 'user' else 'admin'

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 检查重复
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({"code": 400, "message": "用户名已存在"})
            
            # 写入数据
            sql = "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)"
            cursor.execute(sql, (username, password, mapped_role))
        conn.commit()
        return jsonify({"code": 200, "message": "注册成功"})
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)})
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT username, role FROM users WHERE username = %s AND password_hash = %s"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
            
            if user:
                cursor.execute("UPDATE users SET last_login = NOW() WHERE username = %s", (username,))
                conn.commit()
                # 转换角色标识回前端
                role_to_frontend = 'admin' if user['role'] == 'admin' else 'user'
                return jsonify({"code": 200, "role": role_to_frontend})
            else:
                return jsonify({"code": 401, "message": "账号或密码错误"})
    finally:
        conn.close()

# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(chat_bp, url_prefix='/api')
app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')  # 取消注释，注册知识库蓝图

if __name__ == '__main__':
    # 从配置文件读取运行参数
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)