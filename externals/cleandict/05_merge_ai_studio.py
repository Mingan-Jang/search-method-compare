import json
import glob
from pathlib import Path

# ================== 設定區 ==================
downloads_path = Path(r"C:\Users\User\Downloads")
base_path = Path(__file__).parent
output_file = base_path / 'dict_regions_4_merged.json'
merge_log_file = base_path / 'merge_log.txt'

# ===========================================

# 1. 讀取既有的 merged JSON（如果存在）
merged_data = []
if output_file.exists():
    print(f"📖 讀取既有的: {output_file.name}")
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            merged_data = json.load(f)
        print(f"  ✅ 既有資料: {len(merged_data)} 條")
    except Exception as e:
        print(f"  ⚠️ 讀取失敗，將從頭開始: {e}")
        merged_data = []

# 2. 讀取已合併的文件記錄
processed_files = set()
if merge_log_file.exists():
    try:
        processed_files = set(merge_log_file.read_text().strip().split('\n'))
        processed_files.discard('')  # 移除空字符串
        print(f"\n📋 已合併的文件記錄: {len(processed_files)} 個")
    except:
        processed_files = set()

# 3. 查找所有 ai_studio_code*.txt 檔案
pattern = str(downloads_path / "ai_studio_code*.txt")
ai_files = sorted(glob.glob(pattern))
print(f"📂 找到 {len(ai_files)} 個 AI Studio 檔案")

# 4. 找出新的文件（未曾合併的）
new_files = []
for file_path in ai_files:
    file_name = Path(file_path).name
    if file_name not in processed_files:
        new_files.append(file_path)

print(f"📌 新增文件: {len(new_files)} 個")

# 5. 合併新的 JSON 資料
new_count = 0
for file_path in new_files:
    file_name = Path(file_path).name
    print(f"\n📖 處理: {file_name}")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()

            # 嘗試解析 JSON
            try:
                data = json.loads(content)

                # 檢查是否為陣列
                if isinstance(data, list):
                    items_count = 0
                    for item in data:
                        if isinstance(item, dict) and 'original' in item:
                            # 直接追加，不去重
                            merged_data.append(item)
                            items_count += 1
                            new_count += 1
                    print(f"  ✅ 新增 {items_count} 條資料")
                else:
                    print(f"  ⚠️ 非陣列格式，跳過")

            except json.JSONDecodeError as e:
                print(f"  ❌ JSON 解析失敗: {e}")

        # 記錄已處理的文件
        processed_files.add(file_name)

    except Exception as e:
        print(f"  ❌ 讀取失敗: {e}")

# 6. 寫入合併結果
print(f"\n📊 統計:")
print(f"   既有資料: {len(merged_data) - new_count}")
print(f"   新增資料: {new_count}")
print(f"   合計資料: {len(merged_data)}")

print(f"\n💾 寫入: {output_file}")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2)

# 7. 更新合併記錄
print(f"💾 更新: {merge_log_file}")
with open(merge_log_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(sorted(processed_files)))

print("\n✅ 完成！")
