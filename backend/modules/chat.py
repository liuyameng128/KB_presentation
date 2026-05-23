from flask import Blueprint, request, jsonify
from database import get_db_conn

chat_bp = Blueprint('chat', __name__)

# 1. 获取某个用户的所有历史对话列表 (用于侧边栏)
@chat_bp.route('/sessions', methods=['GET'])
def get_sessions():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"code": 400, "msg": "缺少user_id"}), 400
    
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            # 按更新时间倒序排列，让最近聊过的在最上面
            sql = "SELECT id, title, update_time FROM chat_sessions WHERE user_id=%s AND is_deleted=0 ORDER BY update_time DESC"
            cursor.execute(sql, (user_id,))
            sessions = cursor.fetchall()
            return jsonify({"code": 200, "data": sessions})
    finally:
        conn.close()

# 2. 开启一个新对话
@chat_bp.route('/sessions', methods=['POST'])
def create_session():
    data = request.json
    user_id = data.get('user_id')
    
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO chat_sessions (user_id, title) VALUES (%s, '新对话')"
            cursor.execute(sql, (user_id,))
            session_id = cursor.lastrowid # 获取刚刚生成的自增ID
            conn.commit()
            return jsonify({"code": 200, "data": {"session_id": session_id}})
    finally:
        conn.close()