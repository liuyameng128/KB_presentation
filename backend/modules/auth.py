from flask import Blueprint, request, jsonify
from database import get_db_conn

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # 验证参数
    if not username or not password:
        return jsonify({"code": 400, "message": "用户名和密码不能为空"}), 400

    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, username, role, real_name FROM users WHERE username=%s AND password_hash=%s"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
            
            if user:
                # 统一返回格式，前端期望 role 字段
                role_to_frontend = 'admin' if user['role'] == 'admin' else 'user'
                return jsonify({
                    "code": 200, 
                    "message": "登录成功", 
                    "role": role_to_frontend,
                    "username": user['username'],
                    "real_name": user.get('real_name', '')
                })
            return jsonify({"code": 401, "message": "用户名或密码错误"}), 401
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500
    finally:
        conn.close()