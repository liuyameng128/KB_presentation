import os
import torch
import requests
import numpy as np
import chromadb
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from database import get_db_conn
import json

class RAGCore:
    def __init__(self):
        self.initialized = False
        # 模型路径
        self.rerank_model_path = "/data/liuyameng/Models/bge-reranker-v2-m3"
        self.llm_model = "qwen2.5:72b"
        
        # ChromaDB 客户端
        self.chroma_client = chromadb.PersistentClient(path="backend/data/chroma_db")
        
        # 定义四路集合，仅保留故障知识库 (KB) 相关的向量维度
        self.collections = {
            "eq_phen": self.chroma_client.get_or_create_collection("kb_eq_phen"),
            "keyword": self.chroma_client.get_or_create_collection("kb_keyword"),
            "cause": self.chroma_client.get_or_create_collection("kb_cause"),
            "solution": self.chroma_client.get_or_create_collection("kb_solution"),
            # "qa": self.chroma_client.get_or_create_collection("kb_qa") # 注释掉问答库
        }

    def _init_models(self):
        """延迟初始化 Reranker 模型"""
        if self.initialized:
            return
        print("[RAG] 🔄 正在加载 Reranker 模型...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.rerank_model_path)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.rerank_model = AutoModelForSequenceClassification.from_pretrained(self.rerank_model_path).to(self.device)
        self.rerank_model.eval()
        self.initialized = True
        print("[RAG] ✅ 加载完成")

    def get_embedding(self, text):
        """调用 Ollama 获取 BGE 向量"""
        text = str(text).strip() if text else "无"
        url = "http://localhost:11435/v1/embeddings"
        payload = {"model": "bge-m3", "input": text}
        r = requests.post(url, json=payload)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]

    def rerank_score(self, query, doc):
        """重排评分逻辑"""
        inputs = self.tokenizer(query, doc, truncation=True, padding=True, max_length=512, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            score = self.rerank_model(**inputs).logits.squeeze().item()
        return score

    def _normalize_text_field(self, x):
        """统一处理列表或空字段"""
        if x is None: return "无"
        if isinstance(x, list):
            return "；".join([str(i).strip() for i in x]) if x else "无"
        return str(x).strip() if x else "无"

    def retrieve_multi_route(self, query, top_k_recall=30):
        """执行 KB 四路向量检索并从数据库获取详情"""
        qv = self.get_embedding(query)
        kb_ids = set()

        # 1. 执行四路召回 (去除了 QA 路径)
        for name, col in self.collections.items():
            res = col.query(query_embeddings=[qv], n_results=top_k_recall)
            for meta in res['metadatas'][0]:
                if meta.get('type') == 'kb':
                    kb_ids.add(meta['db_id'])

        # 2. 从 MySQL 数据库获取完整字段内容
        conn = get_db_conn()
        results = []
        try:
            with conn.cursor() as cursor:
                for db_id in kb_ids:
                    cursor.execute("SELECT * FROM fault_knowledge WHERE id=%s", (db_id,))
                    item = cursor.fetchone()
                    if item:
                        # 构造用于重排的文本，保留 step6 的 build_kb_rerank_text 逻辑
                        rerank_text = (f"设备：{item.get('equipment','')}\n"
                                       f"故障现象：{item.get('phenomenon','')}\n"
                                       f"原因：{self._normalize_text_field(item.get('causes',''))}\n"
                                       f"关键词：{item.get('keywords','')}")
                        score = self.rerank_score(query, rerank_text)
                        results.append({"source": "kb", "score": score, "item": item})
        finally:
            conn.close()
            
        # 3. 按重排得分排序并取前 10 条
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:10]

    def build_answer_prompt(self, query, top_results):
        """完全保留原始 Prompt 逻辑，仅在遍历时移除 QA 分支"""
        blocks = []
        for i, r in enumerate(top_results, 1):
            it = r["item"]
            # 仅处理故障知识 (kb) 类型的块内容
            block = f"""
【候选 {i}｜故障知识】
设备：{it.get('equipment','')}
故障现象：{it.get('phenomenon','')}
原因：{self._normalize_text_field(it.get('causes',''))}
处理措施：{self._normalize_text_field(it.get('solutions',''))}
""".strip()
            blocks.append(block)

        # 原始 Prompt 模板保持不变
        return f"""你是一名电力设备运维领域的专家。

用户故障描述：
【{query}】

以下是从知识库与运维问答中检索到的候选信息（部分可能无关）：

{chr(10).join(blocks)}

请完成：
1. 判断哪些候选与该故障相关；
2. 基于**相关候选内容**，综合给出一条【最终处理建议】；
3. 若均不相关，请回答：
【没有在知识库中检索到与该故障相关的信息。】

要求：
- 不要编造知识库中不存在的处理措施；
- 不要逐条复述候选内容；
- 直接输出最终结论。

最终只输出【处理建议】或【没有在知识库中检索到相关信息】。""".strip()

    def run(self, query):
        """全流程执行：检索 -> 重排 -> 提示词构造 -> LLM 生成"""
        self._init_models()
        # 1. 检索与重排
        results = self.retrieve_multi_route(query)
        # 2. 构造 Prompt
        prompt = self.build_answer_prompt(query, results)
        # 3. 调用 Ollama API (Qwen2.5 72B)
        url = "http://localhost:11435/api/generate"
        payload = {
            "model": self.llm_model, 
            "prompt": prompt, 
            "stream": False, 
            "options": {"temperature": 0, "seed": 21}
        }
        r = requests.post(url, json=payload)
        return r.json()["response"].strip(), results

# 导出单例对象供 chat.py 调用
rag_engine = RAGCore()