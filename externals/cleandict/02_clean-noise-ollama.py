import os
import json
import random
import time
import argparse
import requests
from pathlib import Path

def process_dict():
    # 使用 argparse 解析命令行參數
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", type=int, default=1, help="指定讀取第幾分片 (例如: 1 代表 dict_1.txt)")
    parser.add_argument("--model", default="qwen2.5:7b", help="Ollama 模型名稱")
    parser.add_argument("--ollama_url", default="http://localhost:11434", help="Ollama 服務地址 (預設: http://localhost:11434)")
    args = parser.parse_args()

    # 1. 驗證 Ollama 連接
    print(f"🔗 嘗試連接 Ollama: {args.ollama_url}")
    try:
        resp = requests.get(f"{args.ollama_url}/api/tags", timeout=5)
        if resp.status_code != 200:
            print(f"❌ Ollama 連接失敗 (狀態碼: {resp.status_code})")
            return
        models = resp.json().get("models", [])
        model_names = [m["name"] for m in models]
        print(f"✅ Ollama 已連接，可用模型: {model_names}")

        # 檢查指定的模型是否存在
        if not any(args.model in m for m in model_names):
            print(f"⚠️ 模型 '{args.model}' 未找到，使用第一個可用模型: {model_names[0] if model_names else 'N/A'}")
            if model_names:
                args.model = model_names[0]  # 使用完整的模型名稱（含標籤）
    except Exception as e:
        print(f"❌ 無法連接 Ollama: {e}")
        print(f"   請確保 Ollama 已啟動時，執行: ollama serve")
        return

    base_path = Path(__file__).parent

    # --- 動態設定檔名，根據 --part 序號區分 ---
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

    # 3. 定義 System Instruction
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
1. 仅输出 JSON 数组。
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
务必输出有效的 JSON 格式。"""

    batch_size = 10
    ollama_api = f"{args.ollama_url}/api/generate"

    print(f"🤖 使用模型: {args.model}")
    print(f"📡 API 端點: {ollama_api}\n")

    # 5. 批次執行
    for i in range(start_index, len(lines), batch_size):
        batch = lines[i:i+batch_size]
        success = False
        retry_count = 0
        max_retries = 3

        while not success and retry_count < max_retries:
            try:
                # 構建 Ollama API 請求


                payload = {
                    "model": args.model,
                    "system": sys_instruct, # 指令分離
                    "prompt": f"請處理：{json.dumps(batch, ensure_ascii=False)}",
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 2048, # 增加生成長度，確保 JSON 完整
                        "num_ctx": 4096,     # 限制上下文大小，節省顯存
                        "top_p": 0.9
                    }
                }

                response = requests.post(ollama_api, json=payload, timeout=300)

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get("response", "").strip()

                    if response_text:
                        # 嘗試從回應中提取 JSON
                        try:
                            # 嘗試直接解析
                            batch_result = json.loads(response_text)
                        except json.JSONDecodeError:
                            # 嘗試尋找 JSON 陣列
                            import re
                            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                            if json_match:
                                batch_result = json.loads(json_match.group())
                            else:
                                raise ValueError("無法從回應中提取 JSON")

                        all_results.extend(batch_result)

                        # 寫入分片專屬的成果與進度檔
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(all_results, f, ensure_ascii=False, indent=2)
                        checkpoint_file.write_text(str(i + len(batch)))

                        print(f"✅ [分片 {args.part}] 已處理: {i + len(batch)} / {len(lines)}")
                        success = True
                else:
                    print(f"⚠️ [分片 {args.part}] Ollama 返回狀態碼: {response.status_code}")
                    print(f"   回應: {response.text[:200]}")
                    retry_count += 1

                time.sleep(3 + random.uniform(1.0, 3.0))

            except requests.exceptions.Timeout:
                print(f"⚠️ [分片 {args.part}] 請求超時 (索引 {i})")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"⏳ {2 * retry_count} 秒後重試... ({retry_count}/{max_retries})")
                    time.sleep(2 * retry_count)
            except requests.exceptions.ConnectionError:
                print(f"❌ [分片 {args.part}] 無法連接 Ollama (索引 {i})")
                print(f"   請檢查 Ollama 是否運行中: {args.ollama_url}")
                return
            except Exception as e:
                print(f"⚠️ [分片 {args.part}] 錯誤 (索引 {i}): {e}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"⏳ {2 * retry_count} 秒後重試... ({retry_count}/{max_retries})")
                    time.sleep(2 * retry_count)

        if not success:
            print(f"❌ [分片 {args.part}] 批次 {i} 處理失敗，已跳過")

if __name__ == "__main__":
    process_dict()
