import json
from pathlib import Path

# ================== 設定區 ==================
base_path = Path(__file__).parent
dict_file = base_path / 'dict_4.txt'
checkpoint_file = base_path / 'checkpoint_4.txt'
merged_json_file = base_path / 'dict_regions_4_merged.json'
output_file = base_path / 'diff.json'

# ===========================================

print("🔍 開始計算差異...\n")

# 1. 讀取 checkpoint
checkpoint = 0
if checkpoint_file.exists():
    try:
        checkpoint = int(checkpoint_file.read_text().strip())
        print(f"📍 checkpoint 進度: 第 {checkpoint} 行")
    except:
        print("⚠️ checkpoint 讀取失敗")
        exit(1)
else:
    print("❌ 找不到 checkpoint 檔案")
    exit(1)

# 2. 讀取 dict_4.txt，提取前 checkpoint 行的詞彙（待處理的範圍）
processed_in_range = set()  # 在 checkpoint 範圍內已被處理的詞
unprocessed_in_range = set()  # 在 checkpoint 範圍內未被處理的詞

if dict_file.exists():
    with open(dict_file, 'r', encoding='utf-8', errors='ignore') as f:
        all_lines = [line.strip() for line in f if line.strip()]

    print(f"📂 dict_4.txt 共有 {len(all_lines)} 行")

    # 提取前 checkpoint 行的詞彙
    first_checkpoint_lines = all_lines[:checkpoint]
    print(f"📌 計算範圍: 前 {checkpoint} 行")
    print(f"   實際讀取: {len(first_checkpoint_lines)} 行")

    dict_words_in_range = {}  # 存儲詞 -> 完整行資訊
    for idx, line in enumerate(first_checkpoint_lines, 1):
        parts = line.split()
        if parts:
            word = parts[0]
            dict_words_in_range[word] = {
                "line_num": idx,
                "full_line": line
            }
else:
    print("❌ 找不到 dict_4.txt")
    exit(1)

# 3. 讀取 dict_regions_4_merged.json，提取已處理的詞彙
merged_words = set()

if merged_json_file.exists():
    try:
        with open(merged_json_file, 'r', encoding='utf-8') as f:
            merged_data = json.load(f)

        print(f"📊 dict_regions_4_merged.json 共有 {len(merged_data)} 條資料")

        for item in merged_data:
            if isinstance(item, dict) and 'original' in item:
                word = item['original']
                merged_words.add(word)
    except Exception as e:
        print(f"❌ 讀取 merged JSON 失敗: {e}")
        exit(1)
else:
    print("❌ 找不到 dict_regions_4_merged.json")
    exit(1)

# 4. 計算在前 checkpoint 行中已被處理 vs 未被處理的詞
for word in dict_words_in_range.keys():
    if word in merged_words:
        processed_in_range.add(word)
    else:
        unprocessed_in_range.add(word)

print(f"\n📈 在前 {checkpoint} 行中:")
print(f"   已被處理: {len(processed_in_range)} 個詞")
print(f"   未被處理: {len(unprocessed_in_range)} 個詞")
print(f"   總計: {len(processed_in_range) + len(unprocessed_in_range)} 個詞")

# 5. 生成 diff JSON - 詳細列出未被處理的詞
unprocessed_details = []
for word in sorted(unprocessed_in_range):
    unprocessed_details.append({
        "word": word,
        "line_num": dict_words_in_range[word]["line_num"],
        "full_line": dict_words_in_range[word]["full_line"]
    })

diff_result = {
    "metadata": {
        "checkpoint": checkpoint,
        "total_dict_lines": len(all_lines),
        "range_lines": len(first_checkpoint_lines),
        "processed_count": len(processed_in_range),
        "unprocessed_count": len(unprocessed_in_range),
        "coverage_rate": f"{len(processed_in_range) / len(dict_words_in_range) * 100:.2f}%" if dict_words_in_range else "0%"
    },
    "unprocessed_words": sorted(list(unprocessed_in_range))
}

# 寫入 diff.json
print(f"\n💾 寫入: {output_file}")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(diff_result, f, ensure_ascii=False, indent=2)

print("✅ 完成！")
print(f"\n📋 摘要:")
print(f"   - 在前 {checkpoint} 行中")
print(f"   - 已被處理: {len(processed_in_range)} 個詞 ({len(processed_in_range)/len(dict_words_in_range)*100:.2f}%)")
print(f"   - 還需處理: {len(unprocessed_in_range)} 個詞 ({len(unprocessed_in_range)/len(dict_words_in_range)*100:.2f}%)")
