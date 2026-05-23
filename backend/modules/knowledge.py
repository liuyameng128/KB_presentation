import os
import uuid
import json
from pathlib import Path
from flask import Blueprint, request, jsonify
from database import get_db_conn
from utils.vector_manager import vector_manager

# 导入 pipeline 模块
from pipeline.step0ocrtestmore_pdftomd import batch_process_with_filter
from pipeline.step1LumberchunkPreprocessAndChunk import batch_process_md
from pipeline.step2overlap import batch_overlap_excels
from pipeline.step2halfLumberchunk import batch_process_fault_excels
from pipeline.step3faultAnalyzeAndJsonExtract import batch_process_fault_csvs

knowledge_bp = Blueprint('knowledge', __name__)

BASE_DIR = Path("/data/liuyameng/Thesis Work/test")
OCR_RESULTS = BASE_DIR / "OCR_results"
EXCEL_CHUNK = BASE_DIR / "excel_chunk"
OVERLAP_DIR = EXCEL_CHUNK / "overlap"
FAULT_RESULTS = EXCEL_CHUNK / "fault_results"
FINAL_OUT_DIR = EXCEL_CHUNK / "onlychunk2json1"


@knowledge_bp.route('/list', methods=['GET'])
def get_knowledge_list():
    """获取知识库列表"""
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, 
                    chunk_id, 
                    chapter, 
                    equipment, 
                    phenomenon, 
                    causes, 
                    solutions, 
                    keywords, 
                    source_text, 
                    file_name,
                    raw_file_name,
                    create_time 
                FROM fault_knowledge 
                ORDER BY create_time DESC
            """
            cursor.execute(sql)
            result = cursor.fetchall()
            
            # 确保 JSON 字段被正确解析
            for row in result:
                if row.get('causes') and isinstance(row['causes'], str):
                    row['causes'] = json.loads(row['causes'])
                if row.get('solutions') and isinstance(row['solutions'], str):
                    row['solutions'] = json.loads(row['solutions'])
                if row.get('keywords') and isinstance(row['keywords'], str):
                    row['keywords'] = json.loads(row['keywords'])
            
            return jsonify({
                "code": 200, 
                "msg": "获取成功",
                "data": result
            })
    except Exception as e:
        print(f"[!] 获取知识列表失败: {str(e)}")
        return jsonify({"code": 500, "msg": f"数据库查询失败: {str(e)}"}), 500
    finally:
        conn.close()


@knowledge_bp.route('/get/<int:id>', methods=['GET'])
def get_knowledge_by_id(id):
    """获取单条知识详情"""
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, chunk_id, chapter, equipment, phenomenon, 
                    causes, solutions, keywords, source_text, 
                    file_name, raw_file_name, create_time 
                FROM fault_knowledge 
                WHERE id = %s
            """
            cursor.execute(sql, (id,))
            result = cursor.fetchone()
            
            if result:
                # 解析 JSON 字段
                if result.get('causes') and isinstance(result['causes'], str):
                    result['causes'] = json.loads(result['causes'])
                if result.get('solutions') and isinstance(result['solutions'], str):
                    result['solutions'] = json.loads(result['solutions'])
                if result.get('keywords') and isinstance(result['keywords'], str):
                    result['keywords'] = json.loads(result['keywords'])
                return jsonify({"code": 200, "data": result})
            else:
                return jsonify({"code": 404, "msg": "记录不存在"}), 404
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500
    finally:
        conn.close()


@knowledge_bp.route('/add', methods=['POST'])
def add_knowledge():
    """手动添加知识条目"""
    try:
        data = request.json
        
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO fault_knowledge 
                    (equipment, phenomenon, causes, solutions, keywords, source_text, file_name, raw_file_name) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    data.get('equipment'),
                    data.get('phenomenon'),
                    json.dumps(data.get('causes', []), ensure_ascii=False),
                    json.dumps(data.get('solutions', []), ensure_ascii=False),
                    json.dumps(data.get('keywords', []), ensure_ascii=False),
                    data.get('source_text', ''),
                    data.get('file_name', 'manual_add'),
                    data.get('raw_file_name', 'manual_add')
                ))
                conn.commit()
                
                # 同步到向量库
                try:
                    vector_manager.sync_all_from_db()
                except Exception as ve:
                    print(f"向量库同步失败: {ve}")
                
                return jsonify({"code": 200, "msg": "添加成功"})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@knowledge_bp.route('/update/<int:id>', methods=['PUT'])
def update_knowledge(id):
    """更新知识条目"""
    try:
        data = request.json
        
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE fault_knowledge 
                    SET equipment=%s, phenomenon=%s, causes=%s, solutions=%s, 
                        keywords=%s, source_text=%s
                    WHERE id=%s
                """
                cursor.execute(sql, (
                    data.get('equipment'),
                    data.get('phenomenon'),
                    json.dumps(data.get('causes', []), ensure_ascii=False),
                    json.dumps(data.get('solutions', []), ensure_ascii=False),
                    json.dumps(data.get('keywords', []), ensure_ascii=False),
                    data.get('source_text', ''),
                    id
                ))
                conn.commit()
                
                # 同步到向量库
                try:
                    vector_manager.sync_all_from_db()
                except Exception as ve:
                    print(f"向量库同步失败: {ve}")
                
                return jsonify({"code": 200, "msg": "更新成功"})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@knowledge_bp.route('/delete/<int:id>', methods=['DELETE'])
def delete_knowledge(id):
    """删除知识条目"""
    try:
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM fault_knowledge WHERE id=%s", (id,))
                conn.commit()
                
                # 重新同步向量库
                try:
                    vector_manager.sync_all_from_db()
                except Exception as ve:
                    print(f"向量库同步失败: {ve}")
                
                return jsonify({"code": 200, "msg": "删除成功"})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@knowledge_bp.route('/upload_file', methods=['POST'])
def upload_file():
    """上传文件并执行知识提取流程"""
    if 'file' not in request.files:
        return jsonify({"code": 400, "msg": "未找到文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"code": 400, "msg": "文件名为空"}), 400
    
    # 检查文件类型
    allowed_extensions = {'.pdf', '.md', '.txt', '.doc', '.docx'}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        return jsonify({"code": 400, "msg": f"不支持的文件类型: {file_ext}"}), 400
    
    # ========== 修改点：保持原始文件名，不加 UUID 前缀 ==========
    original_filename = file.filename
    # 移除这行：unique_name = f"{file_uuid}_{original_filename}"
    # 直接使用原始文件名，但需要处理重名情况
    upload_filename = original_filename
    
    # 处理重名文件：如果文件已存在，在文件名后添加数字后缀
    upload_path = BASE_DIR / "temp_uploads" / upload_filename
    counter = 1
    while upload_path.exists():
        name_parts = original_filename.rsplit('.', 1)
        if len(name_parts) == 2:
            upload_filename = f"{name_parts[0]}_{counter}.{name_parts[1]}"
        else:
            upload_filename = f"{original_filename}_{counter}"
        upload_path = BASE_DIR / "temp_uploads" / upload_filename
        counter += 1
    
    upload_path.parent.mkdir(exist_ok=True)
    file.save(upload_path)
    print(f"[*] 文件已保存: {upload_filename}")
    
    try:
        # 1. 执行 Pipeline 处理
        print(f"[*] 开始处理文件: {original_filename}")
        
        # 修改点：使用实际保存的文件名进行过滤
        # Step 0: PDF/文档转 Markdown
        # 注意：这里需要根据您的 batch_process_with_filter 函数实现调整
        # 如果该函数支持列表过滤，可以传入 [upload_filename]
        batch_process_with_filter(
            str(upload_path.parent), 
            OCR_RESULTS, 
            file_filter=lambda x: x == upload_filename  # 使用实际保存的文件名
        )
        
        # Step 1: 预处理和分块
        system_prompt_chunk = "输入后，您将收到一个中文文档..."  # 请替换为您的 prompt
        batch_process_md(OCR_RESULTS, OCR_RESULTS / "processed", EXCEL_CHUNK, system_prompt_chunk)
        
        # Step 2: 重叠处理
        batch_overlap_excels(EXCEL_CHUNK, OVERLAP_DIR, overlap_size=150)
        
        # Step 2.5: 故障处理
        batch_process_fault_excels(chunk_dir=OVERLAP_DIR, output_dir=FAULT_RESULTS)
        
        # Step 3: 提取 JSON
        batch_process_fault_csvs(FAULT_RESULTS, FINAL_OUT_DIR)
        
        # 2. 读取并保存到数据库
        all_files = list(FINAL_OUT_DIR.glob("*.json")) + list(FINAL_OUT_DIR.glob("*.jsonl"))
        if not all_files:
            return jsonify({"code": 500, "msg": "流水线未生成结果文件"}), 500
        
        latest_file = max(all_files, key=os.path.getmtime)
        print(f"[*] 正在处理结果文件: {latest_file.name}")
        
        with open(latest_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith('['):
                extracted_data = json.loads(content)
            else:
                extracted_data = [json.loads(line) for line in content.splitlines() if line.strip()]
        
        # 3. 写入数据库
        conn = get_db_conn()
        inserted_count = 0
        try:
            with conn.cursor() as cursor:
                for item in extracted_data:
                    sql = """
                        INSERT INTO fault_knowledge 
                        (chunk_id, chapter, equipment, phenomenon, causes, solutions, 
                         keywords, source_text, file_name, raw_file_name) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        item.get('chunk_id'),
                        item.get('Chapter') or item.get('chapter'),
                        item.get('equipment', '未知设备'),
                        item.get('phenomenon', ''),
                        json.dumps(item.get('causes', []), ensure_ascii=False),
                        json.dumps(item.get('solutions', []), ensure_ascii=False),
                        json.dumps(item.get('keywords', []), ensure_ascii=False),
                        item.get('source_text', ''),
                        original_filename,      # file_name: 原始文件名
                        original_filename       # raw_file_name: 原始文件名
                    ))
                    inserted_count += 1
                conn.commit()
                print(f"[*] 成功插入 {inserted_count} 条记录")
        except Exception as db_e:
            print(f"[!] 数据库写入失败: {str(db_e)}")
            raise db_e
        finally:
            conn.close()
        
        # 4. 同步向量数据库
        try:
            vector_manager.sync_all_from_db()
            print("[*] 向量库同步完成")
        except Exception as ve:
            print(f"[!] 向量库同步失败: {ve}")
        
        # 5. 清理临时文件（可选，如果不想保留上传的文件可以删除）
        # 如果想保留原始文件用于调试，可以注释掉删除代码
        try:
            os.remove(upload_path)
            print(f"[*] 临时文件已删除: {upload_filename}")
        except Exception as e:
            print(f"[!] 删除临时文件失败: {e}")
        
        return jsonify({
            "code": 200, 
            "msg": f"成功处理并入库 {inserted_count} 条故障知识"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"code": 500, "msg": f"处理失败: {str(e)}"}), 500

@knowledge_bp.route('/search', methods=['POST'])
def search_knowledge():
    """搜索知识（基于设备名称或故障现象）"""
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()
        
        if not keyword:
            return get_knowledge_list()
        
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT 
                        id, equipment, phenomenon, causes, solutions, 
                        keywords, source_text, file_name, create_time 
                    FROM fault_knowledge 
                    WHERE equipment LIKE %s OR phenomenon LIKE %s
                    ORDER BY create_time DESC
                """
                like_keyword = f"%{keyword}%"
                cursor.execute(sql, (like_keyword, like_keyword))
                result = cursor.fetchall()
                
                # 解析 JSON 字段
                for row in result:
                    if row.get('causes') and isinstance(row['causes'], str):
                        row['causes'] = json.loads(row['causes'])
                    if row.get('solutions') and isinstance(row['solutions'], str):
                        row['solutions'] = json.loads(row['solutions'])
                    if row.get('keywords') and isinstance(row['keywords'], str):
                        row['keywords'] = json.loads(row['keywords'])
                
                return jsonify({"code": 200, "data": result})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@knowledge_bp.route('/batch_delete', methods=['POST'])
def batch_delete():
    """批量删除知识条目"""
    try:
        data = request.json
        ids = data.get('ids', [])
        
        if not ids:
            return jsonify({"code": 400, "msg": "请选择要删除的记录"}), 400
        
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                placeholders = ','.join(['%s'] * len(ids))
                sql = f"DELETE FROM fault_knowledge WHERE id IN ({placeholders})"
                cursor.execute(sql, ids)
                conn.commit()
                
                # 同步到向量库
                try:
                    vector_manager.sync_all_from_db()
                except Exception as ve:
                    print(f"向量库同步失败: {ve}")
                
                return jsonify({"code": 200, "msg": f"成功删除 {len(ids)} 条记录"})
        finally:
            conn.close()
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@knowledge_bp.route('/stats', methods=['GET'])
def get_stats():
    """获取知识库统计信息"""
    conn = get_db_conn()
    try:
        with conn.cursor() as cursor:
            # 总记录数
            cursor.execute("SELECT COUNT(*) as total FROM fault_knowledge")
            total = cursor.fetchone()['total']
            
            # 按设备分组统计
            cursor.execute("""
                SELECT equipment, COUNT(*) as count 
                FROM fault_knowledge 
                WHERE equipment IS NOT NULL AND equipment != ''
                GROUP BY equipment 
                ORDER BY count DESC 
                LIMIT 10
            """)
            equipment_stats = cursor.fetchall()
            
            return jsonify({
                "code": 200,
                "data": {
                    "total": total,
                    "equipment_stats": equipment_stats
                }
            })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500
    finally:
        conn.close()