import os
import json
import random
import time
import argparse
from pathlib import Path
from openai import OpenAI

def load_env_variables(key_prefix="SILICONFLOW_API_KEY"):
    """載入環境變數並獲取多個 API Key，增加強健性處理"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 修正點：加上 strip() 並移除可能誤入的引號
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")

    # 載入所有多個 API Keys (支持 KEY_1, KEY_2 等編號格式)
    api_keys = []
    counter = 1
    while True:
        key_name = f"{key_prefix}_{counter}"
        target_key = os.environ.get(key_name)
        if not target_key:
            break
        api_keys.append(target_key)
        print(f"🔑 已加載 {key_name} (前 4 碼): {target_key[:4]}...")
        counter += 1

    if not api_keys:
        print(f"❌ 找不到任何 API Key (前綴: {key_prefix})，請檢查 .env 檔案")
        return None

    return api_keys

def process_dict():
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", type=int, default=1, help="指定讀取分片 (如 1 代表 dict_1.txt)")
    args = parser.parse_args()

    # 1. 初始化 SiliconFlow 客戶端 - 載入多個 API Keys
    api_keys = load_env_variables()
    if not api_keys: return

    # 追蹤當前使用的 Key 索引
    current_key_index = 0

    def get_client(key_index=None):
        """取得使用指定 API Key 的客戶端"""
        nonlocal current_key_index
        if key_index is not None:
            current_key_index = key_index
        return OpenAI(
            api_key=api_keys[current_key_index],
            base_url="https://api.siliconflow.com/v1"
        )

    # 修正點：確保模型 ID 正確 (建議先用 Qwen2.5-7B 跑，它是免費區常客)
    model_id = "Qwen/Qwen2.5-7B-Instruct"

    base_path = Path(__file__).parent
    input_file = base_path / f'dict_{args.part}.txt'
    output_file = base_path / f'dict_regions_{args.part}.json'
    checkpoint_file = base_path / f'checkpoint_{args.part}.txt'

    if not input_file.exists():
        print(f"❌ 找不到輸入檔案: {input_file}")
        return

    print(f"📂 正在處理分片 {args.part}: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        # 修正點：增加更嚴謹的行處理邏輯
        lines = []
        for line in f:
            parts = line.strip().split()
            if parts:
                lines.append(parts[0])

    # 3. 恢復進度
    start_index = 0
    all_results = []
    if checkpoint_file.exists() and output_file.exists():
        try:
            start_index = int(checkpoint_file.read_text().strip())
            with open(output_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
            print(f"🔄 分片 {args.part} 從第 {start_index} 筆繼續...")
        except Exception as e:
            print(f"ℹ️ 進度讀取失敗，從頭開始: {e}")

    # 4. System Instruction (保持你的專業規範)
    sys_instruct  = """你是一位专业的“多地语义与本地化专家”。你的任务是將输入的 JSON 数组词汇，转换为指定五个地区的习惯称呼，并严格依照分类规范标注代码。

【地区与字体规范】
- tw: 台湾 (繁体中文，台湾惯用語)
- cn: 中国大陆 (简体中文，大陆惯用語)
- hkmc: 香港/澳门 (繁体中文，优先选用港澳惯用語)
- sg: 新加坡 (简体中文，可能使用英文)
- my: 马来西亚 (简体中文，可能源自马语)

【分类代码范围说明】
IND (实体工业)：电机、化学工程、土木建筑、工业耗材、机械、工厂或实验室制程。
DIG (数字信息)：程序语法、网络协议、云端服务、人工智能、电脑周边组件、信号等。
MED (医药疾病)：医学名词、疾病、处方药、解剖构造、医疗器材、保健食品相关。
HIS (历史政治)：历史事件、政治人物、军事将领、古代思想家、古籍、神话传说、宗教人物。
ENT (影视娱乐)：影视剧名、艺人网红、电子游戏、流行音乐、动漫角色、综艺节目。
LIT (文学成语)：四字成语、经典诗词、名言佳句、文学名著（如：红楼梦）。
LOC (地名坐标)：各类站点名称、街道、行政区、著名景点、各国城市、商圈。
NET (网络用语)：网络迷因、梗图用语、社群平台惯用语、时下流行语、论坛术语。
FOO (食物料理)：原始食材、成品菜名、烹饪方法、餐饮品牌、调味料。
TRA (交通运输)：车辆型号、大众运输工具、路况描述、交通法规、航空与航运术语。
SPO (体育运动)：球类运动、赛事名称、运动员、健身术语、奥运项目。
LAW (法律规范)：法律条文名称、法学术语、罪名、合约术语（如：刑法、诉讼、不当得利）。
ECO (经济金融)：股市、汇率、债券、银行术语、保险、财政政策、人物（如：联准会、降息、ETF）。
NAT (自然科学)：动植物名称（非食材）、天文现象、自然科学原理、地理构造（如：黑洞、光合作用、石英、热力学第二定律）。
OTH (日常生活)：无法归入上述领域、通用的日常生活用品（如：扫帚、衣架）或抽象通用概念、各类物理量与货币单位之通用描述。

【输出限制】
1. 僅能输出 JSON 数组， 嚴格遵守 response_mime_type: "application/json"。
2. 即使各地称呼相同，也必须填入对应的字体（繁体/简体）。
3. 针对词汇特性，从上方代码中选择 1 至 3 个最贴切的放入 cates 数组。
4. 高频通用词或计量单位：无专业背景者（如：雨伞、跑步、多亿、千克），必标 OTH。
5. 若该地区习惯直接使用英文，则保留英文。

【范例】
输入：["马铃薯", "多亿加元"]
输出：
[
  {
    "original": "马铃薯",
    "tw": "馬鈴薯",
    "cn": "土豆",
    "hkmc": "薯仔",
    "sg": "马铃薯",
    "my": "马铃薯",
    "cates": ["FOO", "OTH"]
  },
  {
    "original": "多亿加元",
    "tw": "多億加幣",
    "cn": "多亿加元",
    "hkmc": "多億加元",
    "sg": "多亿加元",
    "my": "多亿加元",
    "cates": ["ECO", "OTH"]
  }
]
"""
    batch_size = 30 # Qwen 8B 處理 30 筆還算輕鬆

    # 5. 批次執行 - 支持多個 API Key
    for i in range(start_index, len(lines), batch_size):
        batch = lines[i:i+batch_size]
        success = False
        retry_count = 0
        keys_tried = set()

        while not success and retry_count < 3 + len(api_keys):
            try:
                # 如果當前 Key 已用盡，切換到下一個 Key
                if current_key_index in keys_tried and retry_count > 0:
                    next_key_index = (current_key_index + 1) % len(api_keys)
                    if next_key_index == current_key_index:
                        # 所有 Key 都已嘗試過
                        print(f"⚠️ [分片 {args.part}] 所有 API Key 都已嘗試，停止重試")
                        break
                    get_client(next_key_index)
                    print(f"🔄 [分片 {args.part}] 切換至 API Key_{current_key_index + 1}")

                keys_tried.add(current_key_index)
                client = get_client()

                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": sys_instruct},
                        {"role": "user", "content": json.dumps(batch, ensure_ascii=False)}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )

                raw_content = response.choices[0].message.content
                if raw_content:
                    parsed_json = json.loads(raw_content)

                    # 修正點：增強對 8B 模型回傳結構的防呆
                    if isinstance(parsed_json, dict):
                        # 如果 AI 回傳 {"data": [...]} 或 {"result": [...]}
                        possible_list = next(iter(parsed_json.values()))
                        if isinstance(possible_list, list):
                            batch_result = possible_list
                        else:
                            # 如果 AI 回傳單個物件而非陣列
                            batch_result = [parsed_json]
                    else:
                        batch_result = parsed_json

                    all_results.extend(batch_result)

                    # 寫入成果
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_results, f, ensure_ascii=False, indent=2)

                    # 更新進度
                    checkpoint_file.write_text(str(i + len(batch)))

                    print(f"✅ [分片 {args.part}] 進度: {i + len(batch)} / {len(lines)} (使用 Key_{current_key_index + 1})")
                    success = True

                time.sleep(0.5)

            except Exception as e:
                retry_count += 1
                error_str = str(e)
                print(f"⚠️ [分片 {args.part}] 錯誤 (索引 {i}, Key_{current_key_index + 1}): {type(e).__name__} - {error_str[:100]}")

                # 偵測 401 或 429 (超限)，嘗試切換 Key
                if "401" in error_str or "Unauthorized" in error_str:
                    print(f"🔐 API Key_{current_key_index + 1} 無效，嘗試切換至下一個 Key...")
                    if (current_key_index + 1) < len(api_keys):
                        get_client((current_key_index + 1) % len(api_keys))
                        time.sleep(2)
                        continue
                    else:
                        print("🛑 所有 API Key 都已無效，停止處理")
                        return
                elif "429" in error_str or "Rate limit" in error_str:
                    print(f"⏱️ Key_{current_key_index + 1} 達到速率限制，切換至下一個 Key...")
                    get_client((current_key_index + 1) % len(api_keys))
                    time.sleep(5)
                    continue

                print(f"⏳ 30 秒後進行第 {retry_count} 次重試...")
                time.sleep(30)

if __name__ == "__main__":
    process_dict()