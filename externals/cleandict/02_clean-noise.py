import os
import json
import random
import time
import argparse
from pathlib import Path
from google import genai
from google.genai import types

def load_all_api_keys():
    """載入所有可用的 API Keys 並回傳"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    # 收集所有 GOOGLE_API_KEY_* 或 GEMINI_API_KEY
    api_keys = []
    for i in range(1, 10):  # 支援到 10 個 key
        key_name = f"GOOGLE_API_KEY_{i}"
        api_key = os.environ.get(key_name)
        if api_key:
            api_keys.append(api_key)

    # 若沒有找到編號的 key，試試通用的 GOOGLE_API_KEY 或 GEMINI_API_KEY
    if not api_keys:
        if os.environ.get("GOOGLE_API_KEY"):
            api_keys.append(os.environ.get("GOOGLE_API_KEY"))
        elif os.environ.get("GEMINI_API_KEY"):
            api_keys.append(os.environ.get("GEMINI_API_KEY"))

    if api_keys:
        print(f"✅ 已載入 {len(api_keys)} 個 API Key")
    else:
        print(f"❌ 找不到任何 API Key，請檢查 .env 檔案")

    return api_keys

def process_dict():
    # 使用 argparse 解析命令行參數
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", type=int, default=1, help="指定讀取第幾分片 (例如: 1 代表 dict_1.txt)")
    args = parser.parse_args()

    # 1. 載入所有可用的 API Keys
    api_keys = load_all_api_keys()
    if not api_keys:
        return

    current_key_index = 0
    model_id = "gemini-2.5-flash-lite"

    base_path = Path(__file__).parent

    # --- 動態設定檔名，根據 --part 序號區分 ---
    # 假設你的檔案叫 dict_1.txt, dict_2.txt...
    input_file = base_path / f'dict_{args.part}.txt'
    output_file = base_path / f'dict_regions_{args.part}.json'
    checkpoint_file = base_path / f'checkpoint_{args.part}.txt'
    # ---------------------------------------

    # 2. 讀取與清理資料
    if not input_file.exists():
        print(f"❌ 找不到輸入檔案: {input_file}")
        return

    print(f"📂 正在處理分片 {args.part}: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        # 只取每行第一個空格前的詞彙
        lines = [line.strip().split()[0] for line in f if line.strip()]

    # 3. 恢復進度
    start_index = 0
    all_results = []
    if checkpoint_file.exists() and output_file.exists():
        try:
            start_index = int(checkpoint_file.read_text().strip())
            with open(output_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
            print(f"🔄 分片 {args.part} 從第 {start_index} 筆繼續處理...")
        except Exception as e:
            print(f"ℹ️ 無法讀取進度，將從頭開始: {e}")

    # 3. 定義 System Instruction 與 Config
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
    batch_size =40

    # 5. 批次執行
    for i in range(start_index, len(lines), batch_size):
        batch = lines[i:i+batch_size]
        success = False

        while not success:
            try:
                # 使用當前的 API Key
                current_api_key = api_keys[current_key_index]
                client = genai.Client(api_key=current_api_key)

                response = client.models.generate_content(
                    model=model_id,
                    contents=json.dumps(batch, ensure_ascii=False),
                    config=types.GenerateContentConfig(
                        system_instruction=sys_instruct,
                        response_mime_type="application/json",
                        temperature=0.1
                    )
                )

                if response.text:
                    batch_result = json.loads(response.text)
                    all_results.extend(batch_result)

                    # 寫入分片專屬的成果與進度檔
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_results, f, ensure_ascii=False, indent=2)
                    checkpoint_file.write_text(str(i + len(batch)))

                    print(f"✅ [分片 {args.part}] 已處理: {i + len(batch)} / {len(lines)} (Key #{current_key_index + 1})")
                    success = True

                time.sleep(2 + random.uniform(0.5, 2.0))

            except Exception as e:
                error_msg = str(e)
                # 檢查是否是 429 限流錯誤
                if "429" in error_msg or "too many requests" in error_msg.lower() or "quota" in error_msg.lower():
                    print(f"⚠️ [分片 {args.part}] 遇到 429 限流錯誤: {e}")
                    # 切換到下一個 API Key
                    current_key_index = (current_key_index + 1) % len(api_keys)
                    print(f"🔑 切換到 API Key #{current_key_index + 1} (共 {len(api_keys)} 個)")
                    time.sleep(5)  # 等待 5 秒後再試
                else:
                    print(f"⚠️ [分片 {args.part}] 錯誤 (索引 {i}): {e}")
                    print("⏳ 1 分鐘後重試...")
                    time.sleep(60)

if __name__ == "__main__":
    process_dict()