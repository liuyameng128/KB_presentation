from .imports import *

class Fault(BaseModel):
    equipment: str
    phenomenon: str # 新增：原文字符片段
    causes: List[str]
    solutions: List[str]
    keywords: List[str]
    
class FaultList(BaseModel):
    fault_cases: List[Fault]


def LLM_chat_ollama_structured(
    user_prompt: str,
    schema: dict,
    model_name="qwen2.5:7b",
    system_prompt: Optional[str] = None,
):
    """
    使用 Ollama Chat API + Structured Outputs(JSON Schema)
    """
    ollama_url = "http://localhost:11435/api/chat"

    messages = []
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": user_prompt
    })

    request_data = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "format": schema,          # ⭐ 核心：JSON Schema
        "options": {
            "temperature": 0.0,
            "seed": 42,
            "num_ctx": 8192
        }
    }

    response = requests.post(
        ollama_url,
        json=request_data,
        timeout=1000.0
    )
    response.raise_for_status()

    result = response.json()

    # Chat API 的内容在这里
    return result["message"]["content"]

def LLM_prompt_ollama(user_prompt, model_name="qwen2.5:7b", system_prompt=None):
    """
    调用本地Ollama服务的统一函数。
    
    参数:
        user_prompt: 用户提示词（即您的文档文本）。
        model_name: 要使用的模型，默认为 'qwen2.5:7b'。
        system_prompt: 系统指令。如果提供，会与user_prompt组合。
    """
    ollama_url = "http://localhost:11435/api/generate"
    
    # 1. 组合提示词：将系统指令和用户文档组合
    full_prompt = ""
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n"
    full_prompt += user_prompt
    
    # 2. 构建请求数据（Ollama API标准格式）
    request_data = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False,  # 我们一次性获取完整响应
        "options": {
            "temperature": 0.0,  # 保持您原有的低随机性设置
            "seed" : 42,
            "num_ctx": 8192
            # 可以在此添加其他模型参数，如 'top_p', 'top_k' 等
        }
    } 
    # 3. 发送请求并处理响应
    try:
        # 设置较长的超时时间，因为本地模型推理可能需要时间
        response = requests.post(ollama_url, json=request_data, timeout=1000.0)
        response.raise_for_status()  # 如果HTTP状态码不是200，则抛出异常
        result = response.json()
        generated_text = result.get("response", "").strip()
        # 调试：可打印部分响应，确认模型工作正常
        # print(f"[Ollama] 收到响应: {generated_text[:100]}...")
        
        return generated_text
        
    except requests.exceptions.ConnectionError:
        print("❌ 错误：无法连接到Ollama服务。请确保Ollama已启动（运行 'ollama serve'）。")
        return "connection_error"
    except requests.exceptions.Timeout:
        print("❌ 错误：请求Ollama服务超时。可能是模型正在加载或输入过长。")
        return "timeout_error"
    except Exception as e:
        print(f"❌ 调用Ollama时发生未知错误: {e}")
        # 可以在此记录更详细的日志
        return f"error: {e}"


def safe_json_loads(text): #安全解析json
    try:
        return json.loads(text)
    except Exception:
        # 尝试截取 JSON 主体
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                return None
        return None
    

PROMPT_JSON = """
        你是一个经验丰富的设备运维与检修技术专家。
        以下内容来自不同故障报告文档、检修文档、或规程文件，
        主要描述设备运行过程中可能出现的故障现象、原因及处理措施。 
        
        文本如下：
        <<<CHUNK_TEXT>>>
        
        提取故障块智能体给出的理由如下：
        <<<REASON_TEXT>>>

        请基于原文，提取“设备-故障-原因-处理措施-关键词”结构化信息，并以 JSON 格式返回：

        {
        "fault_cases": [
            {
            "equipment": "...",
            "phenomenon": "...",
            "causes": ["..."],
            "solutions": ["..."],
            "keywords": ["...", "...", "..."]
            }
        ]
        }
        
        若文本中不存在明确故障信息，请返回：
        {"fault_cases": []}

        要求：
        1. 故障、原因、处理措施必须来自原文
        2. 只作提取，不能改写、不能摘要。
        3. 如果没有内容或未提及就不写，不能编造！
        4. 如果某些字段信息在报告中未提及可以留空，不必须同时存在。
        5. 不要合并不同故障 
        6. 只输出 JSON，不要任何解释
        7. 设备名称要具体明确
        8. 故障现象要简洁完整
        9. 原因和措施用列表形式，有多少提取多少
        10. 关键词要相关且具体（最多5个）  
        11. 保持专业性和准确性 
        **特别提醒**：
        - 仔细识别原因，从报告中提取具体的原因描述,仔细识别因果链条 
        """
 
# chunk_dir = Path("/data/wangsiqi/work1/fault_results/sample") 
# #/data/wangsiqi/work/LumberChunker/fault_results
# output_dir = Path("/data/wangsiqi/work1/LumberChunker/chunk2json1")
# output_dir.mkdir(exist_ok=True)

# for chunk_file in sorted(chunk_dir.glob("*.csv")):
    
def process_single_fault_csv(
    chunk_file: Path,
    output_dir: Path,
    system_prompt: str = None,
    model_name="qwen2.5:7b",
):
    print(f"\n开始处理文件:{chunk_file.name}")
    base_name = chunk_file.name
    output_path = output_dir / f"{base_name}_json_result.jsonl" 
    # ===== 断点保护（可选）=====
    if output_path.exists():
        print(f"⚠️ 已存在结果，跳过：{output_path.name}")
        # continue
        return
    #逐chunk执行
    try:
        df = pd.read_csv(chunk_file)
        if df.empty:
            # continue.
            print("空文件，跳过")
            return
    except (pd.errors.EmptyDataError, FileNotFoundError):
        print(f"❌ 读取失败，跳过：{chunk_file}")
        return
        
    results = []
    schema = FaultList.model_json_schema()
    
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        chunk_id = row["chunk_id"]
        chapter = row["Chapter"]
            
        chunk_text = str(row["fault_text"]) if pd.notna(row["fault_text"]) else ""
        reason_text = str(row["reason"]) if pd.notna(row["reason"]) else ""

        prompt_json = PROMPT_JSON.replace("<<<CHUNK_TEXT>>>", chunk_text).replace("<<<REASON_TEXT>>>", reason_text)
        
        resp_json = LLM_chat_ollama_structured(
            user_prompt=prompt_json,
            model_name=model_name,
            schema=schema,
            system_prompt=system_prompt,
        )
        
        fault_list = FaultList.model_validate_json(resp_json)
        if not fault_list.fault_cases:
            continue
        
        for i, fault in enumerate(fault_list.fault_cases):
            try:  
                results.append({
                    # "chunk_id": idx,
                    "chunk_id":chunk_id,
                    "Chapter": chapter, 
                    "equipment": fault.equipment,
                    "phenomenon": fault.phenomenon,
                    "causes": fault.causes,
                    "solutions": fault.solutions,
                    "keywords": fault.keywords,  
                    "source_text":chunk_text,
                    "file_name": chunk_file.name,
                }) 
            except Exception:
                continue
    
    if results: 
        with open(output_path, "w", encoding="utf-8") as f: 
            json.dump(results, f, ensure_ascii=False, indent=2) 
        print(f"✅ JSONL 已保存: {output_path}")
    else:
        print("⚠️ 本文件未抽取到任何结果")

# except (pd.errors.EmptyDataError, FileNotFoundError):
#     print(f"跳过文件: {chunk_file}")
#     continue

def batch_process_fault_csvs(
    chunk_dir: Path,
    output_dir: Path,
    system_prompt: str = None,
    model_name="qwen2.5:7b",
):
    output_dir.mkdir(parents=True,exist_ok=True)

    for chunk_file in sorted(chunk_dir.glob("*.csv")):
        process_single_fault_csv(
            chunk_file=chunk_file,
            output_dir=output_dir,
            system_prompt=system_prompt,
            model_name=model_name,
        )
