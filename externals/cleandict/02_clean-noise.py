import os
import json
import random
import time
import argparse
from pathlib import Path
from google import genai
from google.genai import types

def load_env_variables(key_name="GOOGLE_API_KEY"):
    """載入環境變數並根據參數選擇 API Key"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

    # 核心邏輯：根據輸入的參數決定要用哪一個 Key
    target_key = os.environ.get(key_name)
    if target_key:
        os.environ["GEMINI_API_KEY"] = target_key
        print(f"🔑 使用 API Key 來源: {key_name}")
    else:
        # 如果找不到指定的 Key，就嘗試用預設的
        print(f"⚠️ 找不到環境變數 {key_name}，請檢查 .env 檔案")

def process_dict():
    # 使用 argparse 解析命令行參數
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_key", default="GOOGLE_API_KEY", help="指定要使用的 API Key 變數名稱")
    parser.add_argument("--part", type=int, default=1, help="指定讀取第幾分片 (例如: 1 代表 dict_1.txt)")
    args = parser.parse_args()

    # 1. 初始化環境與 Client
    load_env_variables(args.use_key)
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model_id = "gemini-flash-lite-latest"

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
    sys_instruct = """
    你是一位專業的「多地語義與在地化專家」。你的任務是將輸入的 JSON 陣列詞彙，轉換為指定五個地區的習慣稱呼，並嚴格依照分類規範標註代碼。

【地區與字體規範】
- tw: 台灣 (繁體中文，台灣慣用語)
- cn: 中國大陸 (簡體中文，大陸慣用語)
- hkmc: 香港/澳門 (繁體中文，優先選用港澳慣用語)
- sg: 新加坡 (簡體中文，可能混用英文)
- my: 馬來西亞 (簡體中文，可能源於馬來語)

【分類代碼範圍說明】
IND (實體工業)：電機、化學工程、土木建築、工業耗材、機械、工廠或實驗室製程。
DIG (數位資訊)：程式語法、網路協議、雲端服務、人工智慧、電腦周邊組件、訊號等。
MED (醫藥疾病)：醫學名詞、疾病、處方藥、解剖構造、醫療器材、保健食品相關。
HIS (歷史政治)：歷史事件、政治人物、軍事將領、古代思想家、古籍、神話傳說、宗教人物。
ENT (影視娛樂)：影視劇名、藝人網紅、電子遊戲、流行音樂、動漫角色、綜藝節目。
LIT (文學成語)：四字成語、經典詩詞、名言佳句、文學名著（如：紅樓夢）。
LOC (地名座標)：各類站點名稱、街道、行政區、著名景點、各國城市、商圈。
NET (網路用語)：網路迷因、梗圖用語、社群平台慣用語、時下流行語、論壇術語。
FOO (食物料理)：原始食材、成品菜名、烹飪方法、餐飲品牌、調味料。
TRA (交通運輸)：車輛型號、大眾運輸工具、路況描述、交通法規、航空與航運術語。
SPO (體育運動)：球類運動、賽事名稱、運動員、健身術語、奧運項目。
LAW (法律規範)：法律條文名稱、法學術語、罪名、合約術語（如：刑法、訴訟、不當得利）。
ECO (經濟金融)：股市、匯率、債券、銀行術語、保險、財政政策、人物（如：聯準會、降息、ETF）。
NAT (自然科學)：動植物名稱（非食材）、天文現象、自然科學原理、地理構造（如：黑洞、光合作用、石英、熱力學第二定律）。
OTH (日常生活)：無法歸入上述領域、通用的日常生活用品（如：掃帚、衣架）或抽象通用概念。

【輸出限制】
1. 僅輸出 JSON 陣列。
2. 嚴格遵守 response_mime_type: "application/json"。
3. 即使各地稱呼相同，也必須填入對應的字體（繁體/簡體）。
4. 針對詞彙特性，從上方代碼中選擇 1 至 3 個 最貼切的放入cates陣列。
5. 高頻通用詞：Google 搜尋量預計 > 1,000 萬筆且無專業背景者（如：雨傘、跑步），必標 OTH。

【範例】
輸入：["馬鈴薯"  , "優步"]
輸出：
[
{
    "original": "馬鈴薯",
    "tw": "馬鈴薯",
    "cn": "土豆",
    "hkmc": "薯仔",
    "sg": "马铃薯",
    "my": "马铃薯",
    "cates": ["FOO", "OTH"]
  },
  {
  "original": "Uber",
  "tw": "優步",
  "cn": "优步",
  "hkmc": "Uber",
  "sg": "优步",
  "my": "Uber",
  "cates": ["TRA", "DIG" , "OTH"]
}
]
    """
    batch_size = 30

    # 5. 批次執行
    for i in range(start_index, len(lines), batch_size):
        batch = lines[i:i+batch_size]
        success = False

        while not success:
            try:
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

                    print(f"✅ [分片 {args.part}] 已處理: {i + len(batch)} / {len(lines)}")
                    success = True

                time.sleep(2 + random.uniform(0.5, 2.0))

            except Exception as e:
                print(f"⚠️ [分片 {args.part}] 錯誤 (索引 {i}): {e}")
                print("⏳ 1 分鐘後重試...")
                time.sleep(60)

if __name__ == "__main__":
    process_dict()