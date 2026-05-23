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

    # response = requests.post(
    #     ollama_url,
    #     json=request_data,
    #     timeout=1000.0
    # )
    # response.raise_for_status()

    try:
        response = requests.post(ollama_url, json=request_data, timeout=1000) # 缩短到 300s，不行就跳过
        response.raise_for_status()
        # return response.json().get("response", "")
    except requests.exceptions.Timeout:
        print("Ollama 响应超时，该块可能过于复杂，已跳过。")
        return "" # 返回空，由上层逻辑处理
    except Exception as e:
        print(f"❌ 请求出错: {e}")
        return ""

    result = response.json()

    # Chat API 的内容在这里
    return result["message"]["content"]

PROMPT_JSON = """
        你是一个经验丰富的设备运维与检修技术专家。
        以下内容来自不同故障报告文档、检修文档、或规程文件，
        主要描述设备运行过程中可能出现的故障现象、原因及处理措施。 
        
        文本如下：
        <<<CHUNK_TEXT>>>

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


# # chunk_dir = Path("/data/wangsiqi/work/LumberChunker/md_sample2/chunk") 
# chunk_dir = Path("/data/wangsiqi/work1/LumberChunker/overlap1") 
# output_dir = Path("/data/wangsiqi/work1/LumberChunker/onlychunk2json1")
# output_dir.mkdir(exist_ok=True)
# print("运行")
# for chunk_file in sorted(chunk_dir.glob("*.xlsx")):
    
def process_single_chunk_excel(
    chunk_file: Path,
    output_dir: Path,
    system_prompt: str,
    model_name="qwen2.5:7b",
):
    print(f"\n开始处理文件:{chunk_file.name}")
    base_name = chunk_file.stem.replace("Ollama_Chunks_-_","")
    output_json = output_dir / f"{base_name}_json_result.json"
    # save_path = output_dir / f"{base_name}_json_results.jsonl"
    # ===== 断点保护（可选）=====
    if output_json.exists():
        print(f"⚠️ 已存在结果，跳过：{output_json.name}")
        # continue
        return
    #逐chunk执行
    df = pd.read_excel(chunk_file)
    results = []
    
    schema = FaultList.model_json_schema()
    
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        chapter = row["Chapter"]
        chunk_text = row["Chunk"]

        # ===== 阶段 2.1：是否存在故障 ===== 
        prompt_json = PROMPT_JSON.replace("<<<CHUNK_TEXT>>>", str(chunk_text))
         
        resp_json = LLM_chat_ollama_structured(
            user_prompt=prompt_json,
            model_name=model_name,
            schema=schema
        )
        
        # fault_list = FaultList.model_validate_json(resp_json)
        try:
            fault_list = FaultList.model_validate_json(resp_json)
        except Exception as e:
            print(f"⚠️ 块 {idx} JSON解析失败（可能输出过长截断或幻觉）。错误信息: {e}")
            # 记录原始错误响应，方便调试
            with open("error_resp.txt", "w") as f:
                f.write(resp_json)
            continue  # 跳过这一块，继续处理下一块

        if not fault_list.fault_cases:
            continue
        
        for i, fault in enumerate(fault_list.fault_cases):
            try:  
                results.append({
                    "chunk_id": idx,
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
    
    if not results:
        print("没有提取到结构化故障")
        # continue
        return
    
    with open(output_json, 'w', encoding='utf-8-sig') as f: 
        json.dump(results, f, ensure_ascii=False, indent=2) 
    
    print(f"✅ 输出完成 → {output_json}")
    
def batch_process_chunk_excels(
    chunk_dir: Path,
    output_dir: Path,
    system_prompt: str,
    model_name="qwen2.5:7b",
):
    output_dir.mkdir(parents=True,exist_ok=True)

    for chunk_file in sorted(chunk_dir.glob("*.xlsx")):
        process_single_chunk_excel(
            chunk_file=chunk_file,
            output_dir=output_dir,
            system_prompt=system_prompt,
            model_name=model_name
        )
