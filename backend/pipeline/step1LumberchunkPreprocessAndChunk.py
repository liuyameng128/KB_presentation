from .imports import *

#文档段落智能分割程序。用llm自动识别一篇英文文档中内容主题发生明显变化的第一段落，
#从而实现智能分段。
def count_words(input_string):
    words = input_string.split()
    return round(1.2*len(words))

# Function to add IDs
def add_ids(row):
    global current_id
    # Add ID to the chunk
    row['Chunk'] = f'ID {current_id}: {row["Chunk"]}'
    current_id += 1
    return row

# You will receive as input an english document with paragraphs identified by 'ID XXXX: <text>'.
# Task: Find the first paragraph (not the first one) where the content clearly changes compared to the previous paragraphs.
# Output: Return the ID of the paragraph with the content shift as in the exemplified format: 'Answer: ID XXXX'.
# Additional Considerations: Avoid very long groups of paragraphs. Aim for a good balance between identifying content shifts and keeping groups manageable.

system_prompt = """
输入后，您将收到一个中文文档，其中有以‘ID XXXX: <text>’标识的段落。
任务：找到第一个段落（不是第一个），其内容与前几个段落相比有明显的变化。
Output：返回内容移位的段落的ID，如示例格式：‘Answer: ID XXXX’。
请注意：避免将过长的段落划为一组，需要在识别内容变化和保持组块大小合理之间取得平衡。
除非有明确的语义边界，否则不要分割。主题一致时，喜欢较大的分块。
"""

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
            num_ctx:8192
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

def markdown_to_structured_df(md_file_path, book_name="技术文档"):
    """
    将Markdown文件按标题层级解析为结构化的DataFrame。
    每个顶级标题(#)下的内容作为一个独立的Chunk。
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用正则表达式按标题分割，同时保留标题文本
    # 模式匹配： (标题标记) (标题文字)， 例如：## 1.1 安全规范
    pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    splits = []
    last_pos = 0
    chapters = []
    
    for match in pattern.finditer(content):
        # 保存上一个标题到当前标题之间的内容
        start = last_pos
        end = match.start()
        chunk_content = content[start:end].strip()
        if chunk_content:
            splits.append(chunk_content)
            # 使用前一个匹配的标题作为本章节名（首个块可能为空）
            chapter = chapters[-1] if chapters else "前言"
            chapters.append(chapter)
        # 记录当前标题作为下一个块的章节名
        chapters.append(match.group(2))  # 标题文字
        last_pos = match.start()
    
    # 处理最后一个标题之后的内容
    final_content = content[last_pos:].strip()
    if final_content:
        splits.append(final_content)
        chapters.append(chapters[-1] if chapters else "全文")

    # 构建DataFrame
    df = pd.DataFrame({
        'Book Name': [book_name] * len(splits),
        'Book ID': [0] * len(splits),
        'Chunk ID': list(range(len(splits))),
        'Chapter': chapters[:len(splits)],  # 对齐
        'Chunk': splits  # 注意：这里保留完整的Markdown格式
    })
    return df

def count_tokens_for_qwen(text):
    """
    精确计算文本的token数量，适用于Qwen等使用类GPT分词器的模型。
    """
    try:
        # 使用 cl100k_base 编码（GPT-4、Qwen系列等使用），这是最准确的近似。
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        # 如果失败，回退到 gpt2 编码，总比单词计数准。
        encoding = tiktoken.get_encoding("gpt2")
    return len(encoding.encode(text))

def markdown_to_structured_by_all_headings_df(md_file_path, book_name="技术文档", max_chunk_chars=1000):
    """
    将Markdown文件按所有层级的标题进行解析和分割。
    每个标题（#、##、###等）下的内容作为一个独立的Chunk，并记录完整标题路径。
    max_chunk_chars: 单个内容块允许的最大字符数，用于防止过长。
    """
    with open(md_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    chunks = []          # 存储每个块的文本内容
    chapters = []        # 存储每个块的完整标题路径
    current_chunk = []   # 临时累积当前块的行
    current_hierarchy = [] # 临时存储当前的标题层级栈，例如 ['# 总则', '## 1.1 范围']
    
    for line in lines:
        line_stripped = line.rstrip('\n')
        # 判断是否为标题行
        match = re.match(r'^(#{1,6})\s+(.+)$', line_stripped)
        
        if match:
            # 遇到新标题，先将之前累积的内容保存为一个块
            if current_chunk:
                chunk_text = ''.join(current_chunk).strip()
                if chunk_text: # 确保有内容
                    # 可选：如果单个块过长，进行二次分割
                    sub_chunks = split_large_chunk_by_token(chunk_text, max_chunk_chars) if max_chunk_chars else [chunk_text]
                    for sub_chunk in sub_chunks:
                        chunks.append(sub_chunk)
                        # 章节名为当前层级栈的最后一个标题（即直接父标题）
                        chapter_name = current_hierarchy[-1] if current_hierarchy else "文档根"
                        chapters.append(chapter_name)
                current_chunk = []
            
            # 处理新标题的层级
            new_title_level = len(match.group(1)) # ‘#’的数量代表层级
            new_title_text = match.group(2)
            
            # 更新层级栈：移除同级或更低级的旧标题，加入新标题
            while current_hierarchy and len(current_hierarchy[-1].split()[0]) >= new_title_level:
                current_hierarchy.pop()
            current_hierarchy.append(f"{'#' * new_title_level} {new_title_text}")
            
            # 将标题行本身作为新块的开始（这样块内就包含了标题）
            current_chunk.append(line)
        else:
            # 非标题行，累积到当前块
            current_chunk.append(line)
    
    # 处理文档最后一部分内容
    if current_chunk:
        chunk_text = ''.join(current_chunk).strip()
        if chunk_text:
            sub_chunks = split_large_chunk_by_token(chunk_text, max_chunk_chars) if max_chunk_chars else [chunk_text]
            for sub_chunk in sub_chunks:
                chunks.append(sub_chunk)
                chapter_name = current_hierarchy[-1] if current_hierarchy else "文档根"
                chapters.append(chapter_name)
    
    # 构建DataFrame
    df = pd.DataFrame({
        'Book Name': [book_name] * len(chunks),
        'Book ID': [0] * len(chunks),
        'Chunk ID': list(range(len(chunks))),
        'Chapter': chapters,  # 这里存储的是直接父级标题，如 “## 1.1 范围”
        'Full Path': [' > '.join(current_hierarchy)] * len(chunks) if current_hierarchy else [''] * len(chunks), # 可选：存储完整路径
        'Chunk': chunks
    })
    return df

def split_large_chunk(text, max_chunk_chars):
    '''
    将过长的文本块按段落（换行符）或句子进行二次分割。
    这是一个简单实现，可据需优化。
    '''
    if len(text) <= max_chunk_chars:
        return [text]
    
    chunks = []
    # 尝试按段落分割
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    current_chunk = []
    current_length = 0
    
    for para in paragraphs:
        para_length = len(para)
        # 如果当前段落本身就已经超长，强制拆分
        if para_length > max_chunk_chars:
            # 先把之前累积的块保存
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_length = 0
            # 对超长段落按句号、分号等进一步分割（简易版）
            sentences = re.split(r'[。；！？]\s*', para)
            sub_para = []
            sub_len = 0
            for sent in sentences:
                if sent:
                    sent_len = len(sent)
                    if sub_len + sent_len > max_chunk_chars and sub_para:
                        chunks.append(''.join(sub_para))
                        sub_para = [sent]
                        sub_len = sent_len
                    else:
                        sub_para.append(sent)
                        sub_len += sent_len
            if sub_para:
                chunks.append(''.join(sub_para))
        # 正常段落，累积
        elif current_length + para_length <= max_chunk_chars:
            current_chunk.append(para)
            current_length += para_length
        else:
            # 当前段落加入会导致超限，保存已有块，新起一块
            if current_chunk:
                chunks.append('n\n'.join(current_chunk))
            current_chunk = [para]
            current_length = para_length
    
    # 别忘了最后一个累积的块
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def split_large_chunk_by_token(text, max_tokens=800):
    if count_tokens_for_qwen(text) <= max_tokens:
        return [text]

    lines = text.splitlines()
    chunks = []
    buf = []

    for line in lines:
        buf.append(line)
        if count_tokens_for_qwen('\n'.join(buf)) > max_tokens:
            # 回退一行
            last = buf.pop()
            if buf:
                chunks.append('\n'.join(buf))
            buf = [last]

            # 如果单行本身就超限，硬切
            if count_tokens_for_qwen(last) > max_tokens:
                for i in range(0, len(last), 500):
                    chunks.append(last[i:i+500])
                buf = []

    if buf:
        chunks.append('\n'.join(buf))

    return chunks

# 表格
def html_table_to_matrix(table):
    """
    把 HTML table 转成一个完整的二维矩阵（rowspan 已展开）
    """
    matrix = []
    rowspan_map = {}  # col_idx -> (value, remaining_rows)
    
    for tr in table.find_all("tr"):
        row = []
        col_idx = 0

        # 先处理来自上一行的 rowspan
        while col_idx in rowspan_map:
            value, remaining = rowspan_map[col_idx]
            row.append(value)
            if remaining == 1:
                del rowspan_map[col_idx]
            else:
                rowspan_map[col_idx] = (value, remaining - 1)
            col_idx += 1

        for td in tr.find_all(["td", "th"]):
            text = td.get_text(strip=True)
            rowspan = int(td.get("rowspan", 1))

            row.append(text)

            if rowspan > 1:
                rowspan_map[col_idx] = (text, rowspan - 1)

            col_idx += 1
        matrix.append(row)
    return matrix

#html->md表格
def matrix_to_markdown(matrix):
    if not matrix:
        return ""

    header = matrix[0]
    md = []
    md.append("| " + " | ".join(header) + " |")
    md.append("| " + " | ".join(["---"] * len(header)) + " |")

    for row in matrix[1:]:
        # 对齐列数
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        md.append("| " + " | ".join(row) + " |")
    return "\n".join(md)

#整合：content中所有表格统一转md？？？
def normalize_tables_in_content(content: str):
    soup = BeautifulSoup(content, "html.parser")
    for table in soup.find_all("table"):
        matrix = html_table_to_matrix(table)
        md_table = matrix_to_markdown(matrix)
        table.replace_with(md_table)
    return soup.get_text("\n", strip=True)

# 去除img、空行
def remove_html_images(text: str) -> str:
    # 删除 <div> 包裹的 img
    text = re.sub(
        r'<div[^>]*>\s*<img[^>]*>\s*</div>',
        '',
        text,
        flags=re.IGNORECASE
    )
    return text
def remove_md_images(text: str) -> str:
    return re.sub(r'!\[.*?\]\(.*?\)', '', text)
def remove_extra_blank_lines(text: str) -> str:
    # 多个空行压成一个
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    return text.strip()

def clean_md_text(text: str) -> str:
    text = normalize_tables_in_content(text)
    text = remove_html_images(text)
    text = remove_md_images(text)
    text = remove_extra_blank_lines(text)
    return text


def LC_process_simgle_md2chunk(md_path, out_dir, excel_out_dir, system_prompt):
    print(f"\n🚀 开始处理: {md_path.name}")
    
    with md_path.open("r", encoding="utf-8") as f:
        text = f.read()

    # 1. 预处理与清理
    clean_text = clean_md_text(text)
    out_md_path = out_dir / f"预处理后_{md_path.name}"
    with out_md_path.open("w", encoding="utf-8") as f:
        f.write(clean_text)

    # 2. 结构化解析
    dataset = markdown_to_structured_by_all_headings_df(
        out_md_path,
        book_name=md_path.stem
    )
    paragraph_chunks = dataset.reset_index(drop=True)
    id_chunks = paragraph_chunks['Chunk'].to_frame()

    # 3. 给每个 Chunk 加上 ID 前缀
    global current_id
    current_id = 0
    id_chunks = id_chunks.apply(add_ids, axis=1) 

    chunk_number = 0    # 当前处理的起点索引
    new_id_list = [0]   # 存放最终切分点的 ID 列表，初始为 0
    word_count_aux = []

    # 4. 智能分段核心循环
    while chunk_number < len(id_chunks) - 5:
        # --- ⭐ 关键点 1：在这里提前锁定当前窗口的物理边界 ---
        window_start = chunk_number 
        word_count = 0
        i = 0
        
        # 滑动窗口拼接，直到 token 数接近 4500
        while word_count < 4500 and (window_start + i) < len(id_chunks) - 1:
            i += 1
            current_chunk_text = id_chunks.at[window_start + i - 1, 'Chunk']
            # 这里的 final_document 只是为了算 token
            temp_doc = "\n".join(f"{id_chunks.at[k, 'Chunk']}" for k in range(window_start, window_start + i))
            word_count = count_tokens_for_qwen(temp_doc)
        
        # 确定本轮 LLM 实际看到的终点 ID
        window_end = window_start + i - 1
        final_document = "\n".join(f"{id_chunks.at[k, 'Chunk']}" for k in range(window_start, window_end + 1))
        
        # 5. 调用 LLM
        question = f"\nDocument:\n{final_document}"
        gpt_output = LLM_prompt_ollama(
            user_prompt=question,
            model_name="qwen2.5:7b",
            system_prompt=system_prompt
        )

        # 6. 处理输出与防死循环逻辑
        if "content_flag_increment" in gpt_output:
            # 模型无法处理或要求简单跳过
            chunk_number = window_start + 1
            print(f"⏩ 触发 flag_increment，步进至 {chunk_number}")
        else:
            # 匹配 Answer: ID XXXX 或 ID: XXXX
            match = re.search(r"ID\s*(\d+)", gpt_output)
            
            if match:
                suggested_id = int(match.group(1))
                
                # --- ⭐ 关键点 2：物理区间校验 ---
                # 只有建议 ID 在 (当前起点, 当前窗口终点] 之间才采纳
                if window_start < suggested_id <= window_end:
                    chunk_number = suggested_id
                    print(f"✅ 解析成功: ID {chunk_number}")
                else:
                    # 如果模型回跳（ID < start）或幻觉（ID > end）
                    chunk_number = window_end # 强制推到窗口末尾，保证进度往前走
                    print(f"⚠️ 模型返回 ID {suggested_id} 无效（区间：{window_start}-{window_end}），强制步进至窗口末尾")
            else:
                # 完全没解析到数字
                chunk_number = window_end 
                print(f"❌ 未解析到有效 ID，强制步进至窗口末尾 {chunk_number}")
        
        # 记录本次确定的切分点（防重复记录）
        if chunk_number > new_id_list[-1]:
            new_id_list.append(chunk_number)
        else:
            # 极端保底：如果逻辑走到这里 chunk_number 还没动，强行 +1
            chunk_number += 1
            new_id_list.append(chunk_number)

    # 7. 善后处理：添加最后一个 ID 并生成 Excel
    if new_id_list[-1] < len(id_chunks):
        new_id_list.append(len(id_chunks))

    # 去除 ID 前缀还原文本
    id_chunks['Chunk'] = id_chunks['Chunk'].str.replace(r'^ID \d+:\s*', '', regex=True)

    new_final_chunks = []
    chapter_chunk = []
    for j in range(1, len(new_id_list)):
        start_idx = new_id_list[j-1]
        end_idx = new_id_list[j]
        if end_idx <= start_idx: continue
        
        new_final_chunks.append('\n'.join(id_chunks.iloc[start_idx: end_idx, 0]))
        
        # 记录章节信息
        if paragraph_chunks["Chapter"][start_idx] != paragraph_chunks["Chapter"][end_idx-1]:
            chapter_chunk.append(f"{paragraph_chunks['Chapter'][start_idx]} to {paragraph_chunks['Chapter'][end_idx-1]}")
        else:
            chapter_chunk.append(paragraph_chunks['Chapter'][start_idx])

    df_new_final_chunks = pd.DataFrame({'Chapter': chapter_chunk, 'Chunk': new_final_chunks})
    fileOut = excel_out_dir / f"Chunks_-_{md_path.stem}.xlsx"
    df_new_final_chunks.to_excel(fileOut, index=False)
    
    print(f"✨ {md_path.name} 处理完成！存档至: {fileOut.name}\n" + "-"*30)
    
#主流程 
#处理单个md文件
# def LC_process_simgle_md2chunk(md_path, out_dir, excel_out_dir, system_prompt):
#     print(f"\n开始处理:{md_path.name}")
    
#     with md_path.open("r", encoding="utf-8") as f:
#         text = f.read()

#     clean_text = clean_md_text(text)
#     out_md_path = out_dir / f"预处理后_{md_path.name}"
#     with out_md_path.open("w", encoding="utf-8") as f:
#         f.write(clean_text)

#     dataset = markdown_to_structured_by_all_headings_df(
#         out_md_path,
#         book_name=md_path.stem
#     )

# # dataset = markdown_to_structured_by_all_headings_df(
# #     file_path, 
# #     book_name="锅炉设备检修规程02章_sample"
# # )

# # #文档智能分段系统的完整实现。核心目标是利用llm自动识别文档中的语义边界，
# # #将一本长篇小说的机械分割段落，重新组成更有意义的内容块。 
# # path = rf"/data/wangsiqi/work/LumberChunker"
# # book_name = "锅炉设备检修规程02章_sample_test"
# # fileOut  = f'{path}/Ollama_Chunks_-_{book_name}.xlsx'
#     paragraph_chunks = dataset.reset_index(drop=True)
#     id_chunks = paragraph_chunks['Chunk'].to_frame()
 
#     # Initialize a global variable for current_id and Apply the function along the rows of the DataFrame
#     global current_id
#     current_id = 0
#     id_chunks = id_chunks.apply(add_ids, axis=1) # Put ID: Prefix before each paragraph

#     chunk_number = 0 #起始chunk索引
#     new_id_list = [] #存放llm判定的新切分点ID
#     i = 0 #当前窗口内累计拼接了多少个chunk 
#     word_count_aux = [] #记录最终拼接chunk的token数
#     current_iteration = 0 

#     while chunk_number < len(id_chunks)-5:
#         # print('chunk_number:',chunk_number)
#         word_count = 0
#         i = 0
#         # while word_count < 550 and i+chunk_number<len(id_chunks)-1:
#         while word_count < 4500 and i+chunk_number<len(id_chunks)-1:  #滑动窗口式拼接多个chunk，直到token数接近1200 #之前是3500
#             i += 1
#             final_document = "\n".join(f"{id_chunks.at[k, 'Chunk']}" for k in range(chunk_number, i + chunk_number))
#             word_count = count_tokens_for_qwen(final_document)
    
#         if(i ==1):
#             final_document = "\n".join(f"{id_chunks.at[k, 'Chunk']}" for k in range(chunk_number, i + chunk_number))
#         else:
#             final_document = "\n".join(f"{id_chunks.at[k, 'Chunk']}" for k in range(chunk_number, i-1 + chunk_number))
        
        
#         question = f"\nDocument:\n{final_document}"
#         # print('question:',question) 
#         word_count = count_tokens_for_qwen(final_document)
#         word_count_aux.append(word_count)
#         chunk_number = chunk_number + i-1

#         # prompt = system_prompt + question
#         # gpt_output = LLM_prompt(model_type="ChatGPT", user_prompt=prompt)
#         # 直接将组装好的文档(question)和系统指令(system_prompt)传给新函数
#         gpt_output = LLM_prompt_ollama(  
#             user_prompt=question,          # 这里传入的就是您原来赋给 `question` 变量的文档文本  
#             model_name="qwen2.5:7b",   
#             system_prompt=system_prompt    # 传入系统指令
#         )    #调用llm，让模型返回一个新的切分点ID

#         # For books where there is dubious content, Gemini refuses to run the prompt and returns mistake. This is to avoid being stalled here forever.
#         if gpt_output == "content_flag_increment":
#             # chunk_number = chunk_number + 1
#             window_start = chunk_number
#             window_end = chunk_number + i - 1

#         else:
#             pattern = r"Answer: ID \w+"
#             match = re.search(pattern, gpt_output)  
            
#             if match is None:
#                 print("⚠️ 未解析到 Answer，跳过当前段")
#                 chunk_number += 1
#                 continue
#             else:
#                 gpt_output1 = match.group(0)
#                 print(gpt_output1)
#                 pattern = r'\d+'
#                 match = re.search(pattern, gpt_output1)
#                 # chunk_number = int(match.group())
                
#                 # old_chunk_number = chunk_number
#                 new_chunk_number = int(match.group())

#                 min_valid = window_start
#                 max_valid = window_end

#                 # 1️⃣ 回退
#                 if new_chunk_number < min_valid:
#                     print(f"⚠️ 回退ID {new_chunk_number}，强制+1")
#                     chunk_number = window_start + 1
#                     continue

#                 # 2️⃣ 越界
#                 if new_chunk_number > max_valid:
#                     print(f"⚠️ 越界ID {new_chunk_number}，裁剪")
#                     chunk_number = window_end
#                 else:
#                     chunk_number = new_chunk_number
                
#                 if not new_id_list or chunk_number > new_id_list[-1]:
#                     new_id_list.append(chunk_number)

#                 # if(new_id_list[-1] == chunk_number):
#                 #     chunk_number = chunk_number + 1

#     new_id_list.append(len(id_chunks))

#     # Remove IDs as they no longer make sense here.
#     id_chunks['Chunk'] = id_chunks['Chunk'].str.replace(r'^ID \d+:\s*', '', regex=True)

#     #Create final dataframe from chunks
#     new_final_chunks = []
#     chapter_chunk = []
#     for i in range(len(new_id_list)):
#         # Calculate the start and end indices for slicing aux1
#         start_idx = new_id_list[i-1] if i > 0 else 0
#         end_idx = new_id_list[i]
#         if end_idx <= start_idx:
#             continue  # 防止 0 → 0 这种非法切片
#         new_final_chunks.append('\n'.join(id_chunks.iloc[start_idx: end_idx, 0]))

#         #This is for chunks where Gemini thinks the text should be spanned between 2 different paragraphs
#         if(paragraph_chunks["Chapter"][start_idx] != paragraph_chunks["Chapter"][end_idx-1]):
#             chapter_chunk.append(f"{paragraph_chunks['Chapter'][start_idx]} and {paragraph_chunks['Chapter'][end_idx-1]}")
#         else:
#             chapter_chunk.append(paragraph_chunks['Chapter'][start_idx])

#     # Write new Chunks Dataframe
#     df_new_final_chunks = pd.DataFrame({'Chapter': chapter_chunk, 'Chunk': new_final_chunks})
    
#     book_name = md_path.stem
#     # fileOut = excel_out_dir / f"Ollama_Chunks_-_{book_name}.xlsx"
#     fileOut = excel_out_dir / f"Chunks_-_{book_name}.xlsx"
#     df_new_final_chunks.to_excel(fileOut, index=False)
    
#     print(f"✅ {md_path.name} 处理完成 → {fileOut}")
#     # df_new_final_chunks.to_excel(fileOut, index=False)
#     # print(f"{book_name} Completed!")
    

#遍历所有md文件 
def batch_process_md(md_dir, preprocess_out_dir, excel_out_dir, system_prompt):
    # 确保目录存在
    preprocess_out_dir.mkdir(parents=True, exist_ok=True)
    excel_out_dir.mkdir(parents=True, exist_ok=True)

    # 1. 扫描已处理的结果库 (Excel目录)
    processed_originals = set()
    for excel_file in excel_out_dir.glob("Chunks_-_*.xlsx"):
        # 核心逻辑：从 "Chunks_-_#2机报告.xlsx" 还原回 "#2机报告"
        # 这样我们就能对应上原始文件名了
        pure_name = excel_file.stem.replace("Chunks_-_", "")
        processed_originals.add(pure_name)

    # 2. 只扫描原始目录 (注意：不要扫描 preprocess_out_dir)
    # 如果 preprocess_out_dir 在 md_dir 里面，我们需要在循环中排除它
    all_md_files = list(md_dir.rglob("*.md"))
    
    # 过滤掉已经是“预处理后_”的文件，避免套娃处理
    input_files = [f for f in all_md_files if not f.name.startswith("预处理后_")]

    print(f"📊 任务清单：待处理原始文件 {len(input_files)} 个")
    print(f"⏭️ 已完成数：{len(processed_originals)} 个")

    for md_path in sorted(input_files):
        # md_path.stem 拿到的就是 "#2机2023年小修冷态验收报告"
        if md_path.stem in processed_originals:
            print(f"✅ 已跳过: {md_path.name}")
            continue

        print(f"🚀 开始处理: {md_path.name}")
        
        try:
            # 传入原始 md_path
            # 函数内部应该：
            # 1. 在 preprocess_out_dir 生成 "预处理后_" + md_path.name
            # 2. 在 excel_out_dir 生成 "Chunks_-_" + md_path.stem + ".xlsx"
            LC_process_simgle_md2chunk(md_path, preprocess_out_dir, excel_out_dir, system_prompt)
            
            processed_originals.add(md_path.stem)
            
        except Exception as e:
            # 针对 tiktoken 联网失败的特殊提示
            if "openaipublic" in str(e):
                print(f"❌ 网络异常：tiktoken分词器下载失败。请尝试离线配置或更换计数函数。")
            else:
                print(f"❌ 文件 {md_path.name} 处理发生异常: {e}")
            continue

#最终执行
# def main():
#     md_dir = Path("/data/wangsiqi/work/LumberChunker/3周目/all_md/test")
#     out_dir = md_dir / "processed"
#     excel_out_dir = Path("/data/wangsiqi/work/LumberChunker/3周目/all_md/test/excel_chunk")

#     batch_process_md(md_dir, out_dir, excel_out_dir, system_prompt)

# # if __name__ == "__main__":
# #     main()

def main():
    # 1. 统一根目录（建议使用相对路径或容器内绝对路径）
    base_dir = Path("/data/liuyameng/run_rag") # 假设你在容器里的工作目录
    
    # 2. 修改输入 MD 的目录
    md_dir = base_dir / "all_md/test/OCR_results"
    
    # 3. 修改预处理输出目录
    out_dir = md_dir / "processed"
    
    excel_out_dir = base_dir / "all_md/test/excel_chunk"

    # 打印一下路径，方便调试
    print(f"输入路径: {md_dir.absolute()}")
    print(f"输出路径: {excel_out_dir.absolute()}")

    # 确保目录存在
    out_dir.mkdir(parents=True, exist_ok=True)
    excel_out_dir.mkdir(parents=True, exist_ok=True)

    batch_process_md(md_dir, out_dir, excel_out_dir, system_prompt)

# if __name__ == "__main__":
#     main()