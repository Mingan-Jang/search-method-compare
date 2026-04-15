import json
from pathlib import Path

# ================== 設定區 ==================
base_path = Path(__file__).parent
merged_json_file = base_path / 'dict_regions_4_merged.json'
input_json_file = base_path / 'input.json'  # 新數據輸入
output_file = base_path / 'dict_regions_4_merged.json'

# ===========================================

print("🔍 開始補齊缺失的詞彙...\n")

# 1. 讀取現有的 merged JSON
merged_data = []
existing_originals = set()

if merged_json_file.exists():
    try:
        with open(merged_json_file, 'r', encoding='utf-8') as f:
            merged_data = json.load(f)

        print(f"📂 讀取既有 merged.json: {len(merged_data)} 條")

        # 提取已存在的 original 字段
        for item in merged_data:
            if isinstance(item, dict) and 'original' in item:
                existing_originals.add(item['original'])

        print(f"   已有詞彙: {len(existing_originals)} 個")
    except Exception as e:
        print(f"❌ 讀取 merged.json 失敗: {e}")
        exit(1)
else:
    print("⚠️ 找不到 dict_regions_4_merged.json，將建立新檔案")

# 2. 讀取新的輸入 JSON
new_data = []

if input_json_file.exists():
    try:
        with open(input_json_file, 'r', encoding='utf-8') as f:
            new_data = json.load(f)

        print(f"\n📖 讀取輸入檔案: {len(new_data)} 條")
    except Exception as e:
        print(f"❌ 讀取輸入 JSON 失敗: {e}")
        exit(1)
else:
    print(f"❌ 找不到 {input_json_file}")
    print(f"   請將新數據存為: {input_json_file}")
    exit(1)

# 3. 篩選出新的詞彙（不在 existing_originals 中的）
new_items = []
duplicate_count = 0

for item in new_data:
    if isinstance(item, dict) and 'original' in item:
        word = item['original']
        if word not in existing_originals:
            new_items.append(item)
            existing_originals.add(word)
        else:
            duplicate_count += 1

print(f"\n📊 篩選結果:")
print(f"   新的詞彙: {len(new_items)} 個")
print(f"   重複的: {duplicate_count} 個")

# 4. 按照 original 字段的文字順序排序新詞彙
new_items_sorted = sorted(new_items, key=lambda x: x.get('original', ''))

# 5. 合併到 merged_data
merged_data.extend(new_items_sorted)

print(f"\n📈 合併後:")
print(f"   總計: {len(merged_data)} 條")

# 6. 按 Unicode 排序整個 merged_data
print(f"\n🔤 按 Unicode 排序中...")
merged_data_sorted = sorted(merged_data, key=lambda x: x.get('original', ''))

# 7. 寫入更新後的 merged JSON
print(f"\n💾 寫入: {output_file}")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(merged_data_sorted, f, ensure_ascii=False, indent=2)

print("\n✅ 完成！")
print(f"\n📋 摘要:")
print(f"   - 新增: {len(new_items)} 個詞彙")
print(f"   - 跳過重複: {duplicate_count} 個")
print(f"   - 最終總數: {len(merged_data)} 條")