import chromadb
import requests
import numpy as np
import json
from database import get_db_conn

class VectorManager:
    def __init__(self):
        # 初始化持久化客户端
        self.client = chromadb.PersistentClient(path="backend/data/chroma_db")
        
        # 仅保留故障知识库 (KB) 的四路向量集合
        self.collections = {
            "eq_phen": self.client.get_or_create_collection("kb_eq_phen"),
            "keyword": self.client.get_or_create_collection("kb_keyword"),
            "cause": self.client.get_or_create_collection("kb_cause"),
            "solution": self.client.get_or_create_collection("kb_solution")
            # "qa": self.client.get_or_create_collection("kb_qa") # 已注释
        }

    def get_embedding(self, text):
        """调用 Ollama 获取 BGE 向量"""
        text = str(text).strip() if text else "无"
        url = "http://localhost:11435/v1/embeddings"
        payload = {"model": "bge-m3", "input": text}
        r = requests.post(url, json=payload)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]

    def _flatten_text(self, x):
        """继承 step5 的文本平铺工具，处理数据库中可能的列表或空值"""
        if x is None: return ""
        if isinstance(x, str): return x
        if isinstance(x, list): return " ".join(self._flatten_text(v) for v in x)
        return str(x)

    def sync_all_from_db(self):
        """从 MySQL 数据库读取并同步四路 KB 向量"""
        conn = get_db_conn()
        try:
            with conn.cursor() as cursor:
                # 1. 同步故障知识库 (KB)
                # 确保字段名与你 fault_knowledge 表中的列名一致
                cursor.execute("SELECT id, equipment, phenomenon, keywords, causes, solutions FROM fault_knowledge")
                kb_rows = cursor.fetchall()
                
                print(f"[*] 开始同步知识库，共计 {len(kb_rows)} 条数据...")
                
                for row in kb_rows:
                    kb_id = str(row['id'])
                    # 严格参照 step5 定义的四路文本构建逻辑
                    texts = {
                        "eq_phen": f"{self._flatten_text(row['equipment'])} {self._flatten_text(row['phenomenon'])}",
                        "keyword": self._flatten_text(row['keywords']),
                        "cause": self._flatten_text(row['causes']),
                        "solution": self._flatten_text(row['solutions'])
                    }
                    
                    # 分别存入四个不同的 Chroma 集合
                    for key, text in texts.items():
                        self.collections[key].upsert(
                            ids=[kb_id],
                            embeddings=[self.get_embedding(text)],
                            metadatas=[{"db_id": kb_id, "type": "kb"}],
                            documents=[text]
                        )
                
                # 2. 同步问答库 (QA) - 已根据需求移除
                # print("[*] 跳过 QA 库同步")

                print(f"✅ 四路故障知识向量同步完成！")
        except Exception as e:
            print(f"❌ 同步失败: {str(e)}")
            raise e
        finally:
            conn.close()

# 实例化对象
vector_manager = VectorManager()