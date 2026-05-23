from .imports import *

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
            "num_ctx":8192
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

PROMPT_HAS_FAULT = """
    你是一名火电厂设备检修与故障分析和故障知识结构化专家。

    请阅读下面给出的【文本分块】，判断其中是否【涉及设备故障或缺陷类型或异常工况或失效现象等】
    
    【判定规则】
    满足以下任意一条，即认为“存在故障”：
    1. 出现明确的故障或缺陷名称（如：磨损、腐蚀、泄漏、卡涩、变形等）
    2. 章节或小节标题本身是“故障/缺陷/异常类型”
    3. 文本内容围绕某一故障的处理、预防、修复展开

    请仅以 JSON 格式输出，不要输出任何解释或多余内容：

    {
    "has_fault": true 或 false
    }

    【文本分块】
    <<<CHUNK_TEXT>>>
    """
     
PROMPT_LOCATE_FAULT = """
    你是一名工业设备故障和检修报告结构化分析专家。
    下面给出的文本中包含一条或多条故障/缺陷或异常情况，请输出每一个故障/缺陷或异常情况的字符起始offset 和 offset_preview。
    
    定义：
    - start_offset 是该故障描述在【原始文本字符串】中的字符起始索引（从 0 开始）
    - offset_preview 必须是从原文中逐字复制的一小段连续字符
    - 必须满足：
        原文[start_offset : start_offset + len(offset_preview)] == offset_preview
    严格要求：
    - offset_preview 不允许改写、删减、同义替换 
    
    每一条故障/缺陷/异常情况 可能会包含 故障/缺陷/异常情况现象描述、一个或多个原因、后续处理措施等内容，这些内容需要被合并为一条，不能拆开。
    
    【示例说明】
    【示例1】
    文本：
    "### 2. 常见故障处理
    ### 2.1 省煤器磨损

    2.1.1在安装和维修时，尽量减小省煤器管子与墙之间的距离，使各蛇形管间距离要尽量均匀，避免形成烟气走廊。
    2.1.2在形成烟气走廊地带的弯头及边排管磨损，加装护瓦和刷涂防磨料处理。
    2.1.3在流速过高的地方管子易磨损部位如：弯头处、第二第三排管子、靠后墙的几排管子等加装防磨装置或者护瓦。

    2.1.4及时处理管排管卡或者支吊架松动，定位块脱落缺陷，消除管子振动引起的机械磨损。
    
    2.1.5磨损超标的管子更换。

    2.2省煤器低温段腐蚀

    2.2.1提高排烟温度。

    2.2.2采用抗腐蚀材料。

    2.2.3更换腐蚀深度超标的管子。
    ## 5. 标准安全措施
    ### 1. 风险分析

    1.1测厚、省煤器割管检查时，使用高速锯、电磨、磨光机易伤眼睛。

    1.2使用倒链，易发生脱扣、挤伤，钢丝绳断裂等不安全现象，易发生设备和人身事故。

    1.3在工作中发生人员跌落、扭伤、砸伤等事故。

    1.4使用电焊等电动工具易发生人身触电事故。

    1.5关闭人孔门时碰伤手、竖井内人员被困。

    1.6焊口探伤射线伤人。
    ### 2. 安全措施
    ### 2.1 安全预防措施

    2.1.1工作票内所列安全措施应全面、准确，得到可靠落实后，方可开工。

    2.1.2.开工前班长根据工作情况及职工精神状况确定工作负责人及检修任务并提前通知到本人作好准备。

    2.1.3工作人员高空必须扎安全带，安全带要挂在坚固的构件上。

    2.1.4工作现场照明充足。

    2.1.5气割、电焊作业时，工作现场做好防火措施，严禁吸烟

    2.2使用高速锯、电磨、磨光机要戴防护眼镜。

    2.3倒链和钢丝绳要进行强度试验合格，并在使用前要检查，防止起吊时发生脱扣、断裂等不安全现象。2.4在工作中人员要增强安全意识，相互监督。高空作业扎好安全带。

    2.5进行电焊等电动工具工作时，应在外面设置刀闸开关，并有人监护。不准在受热面上直接电焊及引接地线。工作完毕，及时切断电源。

    2.6关闭前向竖井内呼叫要关闭人孔门、检查是否有人存在，带好防护手套。

    2.7焊口探伤由专业人员操作、无关人员远离现场。"
    
    说明：应识别到"2.1 省煤器磨损"以及"2.2省煤器低温段腐蚀"为开始
    
    正确输出：
    {
    "fault_starts": [
        { "start_offset": 22 , "offset_preview":"2.1 省煤器磨损", }, 
        { "start_offset": 271, "offset_preview":"2.2省煤器低温段腐蚀", },
    ]
    }
    
    【示例2】
    文本：
    "9.05 | 0.60 | 8.77 | 9.37 | 0.60 |
| 8 | 8.75 | 9.32 | 0.57 | 8.73 | 9.32 | 0.59 |
| 9 | 8.80 | 9.38 | 0.58 | 8.65 | 9.23 | 0.58 |
5、缺陷描述：汽门阀芯内部氧化皮较多。原因分析：一是受早期材料特性、制造工艺、运行工况等因素影响，阀碟、衬套、套筒、卡环等材质为F91，阀套内孔导向面为0.02-0.03mm的渗氮层，氮化工艺不能满足600℃高温下的抗氧化需求，长时间运行后，配合面易产生氧化皮，二、是随着机组大小修时对阀杆及阀套进行打磨清理，渗氮层被打磨干净漏出母材F91材质，导致抗氧化性能越来越差，氧化皮生成速度增加，机组频繁启停及深度调峰冷热交替导致氧化皮逐渐脱落卡在阀碟及衬套内部，会造成汽门卡涩。

处理措施及执行情况：对#2机高压主汽阀、高调门、中压联合汽阀进行改造，汽阀内部阀碟、套筒、卡环、定位销等部件进行材质升级，提高材料高温力学性能和抗氧化性能。同时，与阀杆配合的F91套筒+司太立合金内衬套双层结构改为以F92套筒为母

材的内壁喷焊司太立合金一体化结构，提高内衬套强度，抗变形能力更强。
下一步防范措施：1、按照要求定期进行汽门、调门活动试验，防止阀门卡涩。2、大、小修期间对所有汽门、调门进行检修，阀杆与轴套之间氧化皮进行彻底打磨清理，汽门、调门检修周期控制在2年内。

6、缺陷描述：#2机高压旁路阀前电动门内漏。
原因分析：密封面存在硬质颗粒挤压造成的划伤，阀门关闭瞬时存在硬质颗粒卡在阀芯与阀座密封面处，随阀板下移，对整个结合面产生纵向划痕。

处理措施及执行情况：对阀板进行补焊、车削，并对阀板及阀座进行精研处理，压红丹检查密封面验收合格。

下一步防范措施：加强管道清洁度控制，减少管道内硬质杂质，减少由于杂质引起的阀门内漏；提报技术改造，在高旁前电动门前一米处增加一处滤网，滤网密封形式采用自密封结构，保证滤网结合面严密性。

7、缺陷描述：#2机CV2上阀座疏水手动门卡涩，关不动。

原因分析：阀门为球阀，在阀门关闭过程中，杂质卡涩在阀球处，随阀门关闭，对阀门密封面造成磨损，随阀门开关次数增加，密封面磨损程度加大，导致阀门渗漏。

处理措施及执行情况：对阀门中间杂质去除，对阀门进行下线检修研磨，消除阀球磨损，保证阀门严密性。

下一步防范措施：1、开关疏水门时，先关闭疏水截止阀，后关闭疏水球阀，开启疏水门时，先开启疏水球阀，后开启疏水截止阀，减少水流及杂质对阀门的冲击。2、控制主汽门及高调门检修清洁度，减少管道内杂质。
| 检修前 |
| --- |
| 检修后 |
8、缺陷描述：B海水提升泵机械密封漏水。

原因分析：海水系统中有细小硬质颗粒物进入密封面，导致驱动端机械密封动静环磨损严重，机械密封0型圈老化，失去密封弹性，机封密封面漏水。

处理措施及执行情况：更换新机械密封，重新调整密封间隙，更换磨损密封件。

下一步防范措施：加强水泵测温测振、轴承加注润滑脂等定期工作执行。
9、缺陷描述：#2机A旋网冲洗水泵机封套及轴承室非驱动端磨损严重。

原因分析：#2机A旋网冲洗水泵推力轴承采用卡簧定位、固定，无轴肩、凸台设计，转子轴向推力全部作用于卡簧处。由于卡簧强度和钢性不足，运行中易发生磨损、变形，无法承受轴向推力，导致转子整体下沉。转子下沉引起轴配合间隙增加，下导轴承、叶轮口环等部件发生严重磨损。

处理措施及执行情况：更换磨损严重各部件，保证加工后泵轴、口环等备件配合间隙符合设计要求。

下一步防范措施：加强水泵测温测振、轴承加注润滑脂等定期工作执行。"
    
    正确输出：
    {
    "fault_starts": [
        { "start_offset": 131 ,"offset_preview":"5、缺陷描述：汽门阀芯内部氧化皮较多。", }, 
        { "start_offset": 614 ,"offset_preview":"6、缺陷描述：#2机高压旁路阀前电动门内漏。", }, 
        { "start_offset": 848 ,"offset_preview":"7、缺陷描述：#2机CV2上阀座疏水手动门卡涩，关不动。", }, 
        { "start_offset": 1124 ,"offset_preview":"8、缺陷描述：B海水提升泵机械密封漏水。", }, 
        { "start_offset": 1284 ,"offset_preview":"9、缺陷描述：#2机A旋网冲洗水泵机封套及轴承室非驱动端磨损严重。", }, 
    ]
    }
    
    【示例3】
    文本：
    "# 华电莱州发电有限公司 三类缺陷分析报告

编号：QJ-2022-012
| 缺陷名称：#1机#2中联调门关至95%卡涩。 |
| --- |
| 发生时间： 2022年6月18日 一、缺陷详细描述： | 消除时间： 2022年6月19日 | 隶属系统（设备）： #1机#2中联调门 |
| 6月18日10:20，#1机#2中调门10%活动试验过程中发现#1机ICV2调门 在95%附近卡涩，无法关闭。因1机负荷765MW（大于700MW），不具备试验条 件，待条件具备后再进行#1机ICV2调门快关试验。 |
| 二、原因分析： 涩引起。 | 1、2022年6月02日#1机ICV2调门全行程活动试验时卡涩，采取阀门快 关振打方式后阀门活动试验正常。2022年6月18日#1机ICV2调门10%活动试 验时关至95%卡涩，与第一次卡涩位置基本一致，且阀门全开过程无异常（如 图1所示），初步分析阀门卡涩与伺服阀及液压系统无关，为阀门机械部件卡 |  |
| 2、经阀门快关试验后，#2中联调门恢复正常，指令与反馈无偏差。查阅 台账，#1机#2中联门上次解体检修时间为2020年2月#1机组大修时，阀门运 行两年，分析导致中联调门卡涩原因为阀杆、阀套间存在氧化皮（阀杆与阀套 间隙如图ΦD5所示，标准值：0.47-0.52mm；大修时测量值0.47mm），导致阀 门开关卡涩。 |
图1ICV2调门指令与反馈图
图2：中联调门阀杆阀套间隙示意图
| 三、处理措施： 通过#1机#2中联调门快关试验振打，阀门指令与反馈一致，阀门恢复正 常。 |
| --- |
| 四、防范措施及举一反三检查情况： 1、定期进行阀门活动试验，避免阀门长时间不活动造成氧化皮堆积，引 起阀门卡涩。 2、将阀门卡涩缺陷及时录入设备台账，记录异常情况，根据机组检修计 划设置检修项目，有针对性的对汽门、调门进行解体检修。 3、调研厂家阀杆防氧化皮方案，择机进行改造优化。 |
| 五、分场意见（手填）： 签名： |
| 六、生产技术部意见（手填）： 签名： |
注：本报告分场存档，生产技术部备案。"
    
    说明：应识别到"缺陷名称：#1机#2中联调门关至95%卡涩。"为开始。
    
    正确输出：
    {
    "fault_starts": [
        { "start_offset":40 , "offset_preview":"缺陷名称：#1机#2中联调门关至95%卡涩。", }, 
    ]
    }
    
    【示例4】
    文本：
    "### 4.3 常见故障处理
| 序号 | 缺陷现象 | 原因 | 处理办法 |
| --- | --- | --- | --- |
| 1 | 风机振动 | 联轴器找正不好，风机轴与电机轴不 同心 | 重新进行联轴器找正 |
| 1 | 风机振动 | 风机轴承损坏 | 检查轴承进行更换 |
| 1 | 风机振动 | 风机转子不平衡 | 进行现场动平衡 |
| 2 | 风机轴承发热 | 轴承冷却水流量不足或缺失 | 检查风机轴承冷却水 |
| 2 | 风机轴承发热 | 联轴器找正不好 | 重新进行联轴器找正 |
| 2 | 风机轴承发热 | 风机轴承座内孔变形 | 公差过紧，检查轴承座 |
| 2 | 风机轴承发热 | 润滑油过多 | 将运行时的油位降到油位 |
| 2 | 风机轴承发热 | 润滑油不符合要求，轴承损坏 | 更换轴承 |"
    
    说明：应识别到表格的每一行均为开始。
    
    正确输出：
    {
    "fault_starts": [
        { "start_offset":73 , "offset_preview":"风机振动 | 联轴器找正不好，风机轴与电机轴不 同心 | 重新进行联轴器找正", },  
        { "start_offset":120 , "offset_preview":"风机振动 | 风机轴承损坏 | 检查轴承进行更换", }, 
        { "start_offset":153 , "offset_preview":"风机振动 | 风机转子不平衡 | 进行现场动平衡", }, 
        
        { "start_offset":186 , "offset_preview":"风机轴承发热 | 轴承冷却水流量不足或缺失 | 检查风机轴承冷却水", }, 
        { "start_offset":228 , "offset_preview":"风机轴承发热 | 联轴器找正不好 | 重新进行联轴器找正", }, 
        { "start_offset":265 , "offset_preview":"风机轴承发热 | 风机轴承座内孔变形 | 公差过紧，检查轴承座", }, 
        { "start_offset":305 , "offset_preview":"风机轴承发热 | 润滑油过多 | 将运行时的油位降到油位", }, 
        { "start_offset":342 , "offset_preview":"风机轴承发热 | 润滑油不符合要求，轴承损坏 | 更换轴承", }, 
    ]
    }
    
    【示例5】
    文本：
    "## 莱州电厂#1机组当前轴系问题分析

## 1 ．#1轴承间隙电压变化问题分析

2022年4月8日#1机组停机后，#1轴承振动传感器X/Y方向的间隙电压从正常运行状态的-12V左右，变化到-16V左右。数据反应：机组正常运行过程中300MW~1050MW范围，高压胀差在-2.7mm~-1.0mm范围，4月8日停机后，最大高压负胀差为-5.49mm。
图1#1、#2轴承间隙电压与高压胀差趋势图
从图1可以看出，机组并网运行时，高压胀差大致为-2mm，对应的间隙电压大致为-12V。机组停机后，随着高压胀差逐渐在负向增大，#1轴承间隙电压绝对值逐渐增大，#2轴承间隙电压绝对值大致稳定。

经查阅#1轴承附近轴振动测量结构，结合高压胀差与间隙电压之间的变化关系，分析认为高压负胀差较大致使振动涡流传感器相对于转子往机头侧移动，而#1轴承轴振动测量位置靠机头侧存在间隙（如图2，左侧为机头侧），所以胀差的变化，改变了传感器的测量位置，进而出现了间隙电压变化的情况（估计与转子表面涡流的形成有关）。

综上分析，建议冷态安装涡流传感器时，可以在现有涡流传感器位置基础上，往高压侧移动一定距离，确保高压胀差在正负正常区间的间隙电压测量准确性（振动幅值测量准确）。
图2#1轴承涡流传感器安装图
## 2 ．发电机转子轴振动随负荷波动问题分析

机组在正常带负荷运行过程中，出现发电机转子轴振动随负荷一起波动的情况，详见图3。

如图3所示，机组负荷在0~1050MW之间，9Y轴振动在21m~103m之间波动，10X轴振动43m~61m之间波动。

综合图3、图4、图5，还可以看出机组3000rpm空转时，发电机轴振动较小；带负荷后出现振动波动，但轴振动变化的拐点比负荷变化的拐点存在30min 左右的滞后。同时，振动的波动还与励磁电流、无功功率、冷却风温等有一定的相关性。
图3发电机转子轴振动随负荷波动趋势图1（绿色为负荷，红色为9Y轴振动）
图4发电机转子轴振动随负荷波动趋势图2
图5发电机转子轴振动随负荷波动趋势图3
综上各种现象分析，认为：发电机转子存在热变形故障。因为热变形故障与温度密切相关，而温度的变化总是有一个过程，所以才出现振动拐点比负荷拐点滞后的现象。

发电机转子热变形的原因可能有：匝间短路；转子线圈膨胀受阻：冷却系统效果不佳。具体的热变形原因，还需进一步的试验确认。

鉴于目前机组满负荷电机转子轴振动在103m，仍在安全范围内，还可以继续监视运行。后期有临修机会可以通过现场热平衡配重进一步减小最大轴振动值，进而达到改善发电机盖振的目的。待大修机会时，应彻底检查、排除引起发电机转子热变形的故障。

袁超2022年4月11日"
    
    说明：应识别到"缺陷名称：#1机#2中联调门关至95%卡涩。"为开始，并且后续的"二、原因分析"、"三、处理措施"、"四、防范措施及举一反三检查情况"均属于此缺陷的相关信息。
    
    正确输出：
    {
    "fault_starts": [
        { "start_offset":21 , "offset_preview":"## 1 ．#1轴承间隙电压变化问题分析

2022年4月8日#1机组停机后，#1轴承振动传感器X/Y方向的间隙电压从正常运行状态的-12V左右，变化到-16V左右。数据反应：机组正常运行过程中300MW~1050MW范围，高压胀差在-2.7mm~-1.0mm范围，4月8日停机后，最大高压负胀差为-5.49mm。", }, 
        { "start_offset":547 , "offset_preview":"## 2 ．发电机转子轴振动随负荷波动问题分析

机组在正常带负荷运行过程中，出现发电机转子轴振动随负荷一起波动的情况", }, 
    ]
    }
    
    
    【严格要求】 
    - start_offset 按字符序号（Unicode），从文本第 0 个字符开始计算，包含空格、标点和换行符。
    - start_offset 必须是该故障/缺陷相关内容**首次出现的位置**
    - 在 reasoning 字段中，简要说明为什么选择该 start_offset

    文本如下：
    <<<CHUNK_TEXT>>>
"""
 
class Fault(BaseModel):
    start_offset: int
    offset_preview: str # 新增：原文字符片段
    reason: str
class FaultList(BaseModel):
    faults: List[Fault] 
 
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

def verify_offset(text: str, start: int, preview: str) -> bool:
    if start < 0 or start >= len(text):
        return False
    return text[start:start + len(preview)] == preview

def relocate_offset_by_preview(text: str, preview: str):
    idx = text.find(preview)
    return idx if idx != -1 else None


# #主流程
# # chunk_file = rf"/data/wangsiqi/work/LumberChunker/Ollama_Chunks_-_sample3_test_newchunk.xlsx"
# # output_file = rf"/data/wangsiqi/work/LumberChunker/sample3_fault_detection_result_v2.csv"
# # save_path = "/data/wangsiqi/work/LumberChunker/sample_3has_fault_results_v2.json"

# # ================= 配置路径 =================
# # chunk_dir = Path("/data/wangsiqi/work/LumberChunker/md_sample2/chunk") 
# chunk_dir = Path("/data/wangsiqi/work/LumberChunker/md_sample2/chunk/overlap") #overlap
# output_dir = Path("/data/wangsiqi/work/LumberChunker/fault_results")
# output_dir.mkdir(exist_ok=True)

# ================= 遍历所有excel ===============
def batch_process_fault_excels(
    chunk_dir: Union[str, Path],
    output_dir: Union[str, Path],
    model_name="qwen2.5:7b",
):
    """
    对 chunk excel 批量进行故障检测与定位，并输出 csv + jsonl

    Args:
        chunk_dir: 输入 chunk excel 文件夹
        output_dir: 输出结果目录
        model_name: Ollama 模型名
    """
    chunk_dir = Path(chunk_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)

    for chunk_file in sorted(chunk_dir.glob("*.xlsx")):
        print(f"\n🚀 开始处理文件: {chunk_file.name}")

        base_name = chunk_file.stem.replace("Ollama_Chunks_-_", "")
        output_csv = output_dir / f"{base_name}_fault_detection_result.csv"
        save_path = output_dir / f"{base_name}_has_fault_results.jsonl"

        # ===== 断点保护 =====
        if output_csv.exists():
            print(f"⚠️ 已存在结果，跳过：{output_csv.name}")
            continue

        df = pd.read_excel(chunk_file)
        results = []

        for idx, row in tqdm(df.iterrows(), total=len(df)):
            chapter = row["Chapter"]
            chunk_text = row["Chunk"]

            # ===== 阶段 1：是否存在故障 =====
            prompt_21 = PROMPT_HAS_FAULT.replace("<<<CHUNK_TEXT>>>", str(chunk_text))
            resp_21 = LLM_prompt_ollama(prompt_21, model_name=model_name)
            data_21 = safe_json_loads(resp_21)

            with open(save_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "source_file": chunk_file.name,
                    "chunk_id": idx,
                    "Chapter": chapter,
                    "parsed_result": data_21,
                    "raw_response": resp_21,
                    "chunk_text": chunk_text,
                }, ensure_ascii=False) + "\n")

            if not data_21 or data_21.get("has_fault") is not True:
                continue

            # ===== 阶段 2：故障区间定位 =====
            prompt_22 = PROMPT_LOCATE_FAULT.replace("<<<CHUNK_TEXT>>>", chunk_text)
            schema = FaultList.model_json_schema()

            resp_22 = LLM_chat_ollama_structured(
                user_prompt=prompt_22,
                model_name=model_name,
                schema=schema
            )

            # fault_list = FaultList.model_validate_json(resp_22)
            try:
                fault_list = FaultList.model_validate_json(resp_22)
            except Exception as e:
                print(f"⚠️ 块 {idx} JSON 异常(可能是表格过长截断): {e}")
                # 尝试简单的补齐处理，或者直接 continue 跳过
                if "EOF" in str(e):
                    try:
                        # 暴力补齐括号尝试挽救
                        repaired_json = resp_22.strip()
                        if not repaired_json.endswith("]"): repaired_json += "]}"
                        if not repaired_json.endswith("}"): repaired_json += "}"
                        fault_list = FaultList.model_validate_json(repaired_json)
                        print(f"✅ 块 {idx} 已通过补齐括号挽救")
                    except:
                        print(f"❌ 块 {idx} 挽救失败，跳过")
                        continue
                else:
                    continue

            if not fault_list.faults:
                continue

            # ===== offset 校验 / 纠偏 =====
            validated_faults = []
            for fault in fault_list.faults:
                start = fault.start_offset
                preview = fault.offset_preview
                reason = fault.reason

                if not verify_offset(chunk_text, start, preview):
                    real_start = relocate_offset_by_preview(chunk_text, preview)
                    if real_start is None:
                        continue
                    start = real_start

                validated_faults.append({
                    "start": start,
                    "offset_preview": preview,
                    "reason": reason
                })

            validated_faults.sort(key=lambda x: x["start"])

            # ===== 故障文本切片 =====
            for i, fault in enumerate(validated_faults):
                start = fault["start"]
                end = validated_faults[i + 1]["start"] if i < len(validated_faults) - 1 else len(chunk_text)

                fault_text = chunk_text[start:end]

                results.append({
                    "source_file": chunk_file.name,
                    "chunk_id": idx,
                    "Chapter": chapter,
                    "fault_text": fault_text,
                    "start_offset": start,
                    "end_offset": end,
                    "offset_preview": fault["offset_preview"],
                    "reason": fault["reason"]
                })

        df_result = pd.DataFrame(results)
        df_result.to_csv(output_csv, encoding="utf-8_sig", index=False)

        print(f"✅ 完成：{chunk_file.name}，共识别 {len(df_result)} 条故障")