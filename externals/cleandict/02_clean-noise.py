import os
import json
import random
import time
from pathlib import Path
from google import genai
from google.genai import types

def load_env_variables():
    """載入環境變數"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # 同時支援系統變數名稱與 SDK 預設名稱
                    os.environ[key.strip()] = value.strip()
                    if key.strip() == "GOOGLE_API_KEY":
                        os.environ["GEMINI_API_KEY"] = value.strip()

def process_dict():
    load_env_variables()
    
    # 初始化官方新版 Client
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model_id = "gemini-flash-lite-latest"
    
    base_path = Path(__file__).parent
    input_file = base_path / 'dict.txt'
    output_file = base_path / 'dict_regions.json'
    checkpoint_file = base_path / 'checkpoint.txt'

    # 1. 讀取與清理資料
    if not input_file.exists():
        print(f"❌ 找不到輸入檔案")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        # 只取每行第一個空格前的詞彙
        lines = [line.strip().split()[0] for line in f if line.strip()]

    # 2. 恢復進度
    start_index = 0
    all_results = []
    if checkpoint_file.exists() and output_file.exists():
        try:
            start_index = int(checkpoint_file.read_text().strip())
            with open(output_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
            print(f"🔄 從第 {start_index} 筆繼續處理...")
        except: pass

    # 3. 定義 System Instruction 與 Config
    sys_instruct = """
    你是一位專業的「多地語義與在地化專家」。你的任務是將輸入的 JSON 陣列詞彙，轉換為指定五個地區的習慣稱呼，並嚴格依照分類規範標註代碼。

【地區與字體規範】
- tw: 台灣 (繁體中文，使用台灣慣用語)
- cn: 中國大陸 (簡體中文，使用大陸慣用語)
- hkmc: 香港/澳門 (繁體中文，優先選用港澳慣用語，如：火牛、雪櫃)
- sg: 新加坡 (簡體中文，使用星馬地區習慣稱呼)
- my: 馬來西亞 (簡體中文，與新加坡類似但需注意微小差異)

【分類代碼範圍說明】
- IND: 工業硬體。包含：電機、化學工程、土木建築、重型設備、工業耗材、建築結構（如：箱涵）。
- DIG: 資訊數位。包含：軟體應用、程式語法、網路架構、人工智慧、硬體週邊（如：滑鼠）。
- MED: 醫藥疾病。包含：醫學名詞、各類疾病、處方藥物、生理構造、醫療器材。
- HIS: 歷史神話。包含：歷史事件、歷史人物（包括現代政治人物或名人）、古籍、神話傳說。
- LIT: 文學成語。包含：四字成語、經典詩詞、名言佳句、現代或經典書名。
- LOC: 地名座標。包含：各類站點名稱、街道、行政區名稱、著名景點、城市。
- NET: 網路流行語。包含：網路迷因、梗圖用語、社群平台慣用語、時下流行語。
- FOO: 食物料理。包含：原始食材、成品菜名、烹飪方法、各類餐飲品牌與品類。
- TRA: 交通運輸。包含：車輛種類、大眾運輸工具、路況描述、交通規範、航空航運。
- OTH: 日常生活。包含：無法歸入上述明確領域、通用的日常生活用品或通用概念。

【輸出限制】
1. 僅輸出 JSON 陣列。
2. 嚴格遵守 response_mime_type: "application/json"。
3. 即使各地稱呼相同，也必須填入對應的字體（繁體/簡體）。
4. 分類代碼僅能從上述 10 個中選擇，不可自創。

【範例】
輸入：["變壓器", "馬鈴薯"]
輸出：
[
  {
    "original": "變壓器",
    "tw": "變壓器",
    "cn": "变压器",
    "hkmc": "火牛",
    "sg": "变压器",
    "my": "变压器",
    "category": "IND"
  },
  {
    "original": "馬鈴薯",
    "tw": "馬鈴薯",
    "cn": "土豆",
    "hkmc": "薯仔",
    "sg": "马铃薯",
    "my": "马铃薯",
    "category": "FOO"
  }
]
    """

    batch_size = 30 # Flash-Lite 建議批次可稍微拉大

    # 4. 批次執行
    for i in range(start_index, len(lines), batch_size):
        batch = lines[i:i+batch_size]
        success = False  # 標記當前批次是否成功
        
        while not success:
            try:
                # 官方建議的 generate_content 寫法
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

                    # 寫入檔案
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_results, f, ensure_ascii=False, indent=2)
                    checkpoint_file.write_text(str(i + len(batch)))

                    print(f"✅ 已處理: {i + len(batch)} / {len(lines)}")
                    success = True # 成功處理，跳出 while 迴圈
                
                # 正常請求間隔
                jitter = random.uniform(0.5, 3.0) 
                time.sleep(2 + jitter)

            except Exception as e:
                print(f"⚠️ 發生錯誤 (索引 {i}): {e}")
                print("⏳ 正在等待 1 分鐘後重試...")
                time.sleep(60)  # 固定間隔 1 分鐘
                # 不 break，繼續 while 迴圈進行重試

if __name__ == "__main__":
    process_dict()