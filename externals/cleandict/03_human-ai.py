import pyautogui
import time
import json
import random
import subprocess
from pathlib import Path
from collections import defaultdict
import pyperclip

# ================== 設定區 ==================
base_path = Path(__file__).parent
dict_file = base_path / 'dict_4.txt'
checkpoint_file = base_path / 'checkpoint_4.txt'

rows_to_extract = 100                         # 每次提取的行數
base_delay = 3                                # 基礎延遲秒數
loops = 20                                    # 循環次數

# 根據你的螢幕解析度調整（請先用我之前給的 get_mouse_pos.py 抓準確座標）
input_box_pos = (400, 1000)      # 第一個紅框：輸入框位置
run_button_pos = (850, 1084)     # 第二個紅框：運行按鈕位置（目前註解掉）

# 新增：滾輪設定
content_box_pos = (410, 630)      # 第一個紅框：輸入框位置
scroll_amount = -12000            # 負數 = 往下滾（你要的 3000）
scroll_steps = 5                 # 分成幾次滾動（建議 4~8 次，更穩定）

def random_delay(base_secs=7):
    """隨機延遲，避免被偵測為機器人（確保返回值非負）"""
    return max(0, base_secs + random.uniform(-1.5, 2.0))

def copy_to_clipboard(text):
    """使用 pyperclip 處理 Unicode 剪貼板，避免亂碼"""
    try:
        pyperclip.copy(text)
        print("✅ 已成功複製 Unicode 文字到剪貼板")
        return True
    except Exception as e:
        print(f"⚠️ 剪貼板複製失敗: {e}")
        return False

# ===========================================

# 主循環
for loop_count in range(1, loops + 1):
    print(f"\n{'='*60}")
    print(f"🔄 循環 {loop_count}/{loops}")
    print(f"{'='*60}")

    # 讀取 checkpoint
    start_index = 0
    if checkpoint_file.exists():
        try:
            start_index = int(checkpoint_file.read_text().strip())
            print(f"✅ 從第 {start_index} 行繼續執行")
        except:
            print("⚠️ checkpoint 讀取失敗，從頭開始")

    # 讀取字典檔案（明確指定 UTF-8 編碼）
    if not dict_file.exists():
        print(f"❌ 找不到檔案: {dict_file}")
        exit(1)

    with open(dict_file, 'r', encoding='utf-8', errors='ignore') as f:
        all_lines = [line.strip() for line in f if line.strip()]

    print(f"📂 共讀取 {len(all_lines)} 行資料")

    # 取出本次要處理的 100 行
    end_index = min(start_index + rows_to_extract, len(all_lines))
    selected_lines = all_lines[start_index:end_index]

    if not selected_lines:
        print("❌ 已處理完所有資料！結束循環")
        break

    # 解析詞彙（只保留詞，不計算頻數）
    words_list = []
    for line in selected_lines:
        parts = line.split()
        if len(parts) >= 1:
            word = parts[0]
            words_list.append(word)

    # 轉成 JSON 數組格式（用戶需要的格式）
    word_json = json.dumps(words_list, ensure_ascii=False, indent=2)
    print(f"📊 本次準備提交 {len(words_list)} 個詞彙")
    print(f"📝 JSON 預覽: {word_json[:100]}...")

    # ====================== 自動化操作開始 ======================
    print("🖱️ 開始自動操作... 請確保 AI 視窗已開啟且在前台")

    # 移動到輸入框並點擊（確保焦點）
    print(f"🖱️ 移動到輸入框位置 {input_box_pos}")
    pyautogui.moveTo(input_box_pos[0], input_box_pos[1], duration=0.8)
    time.sleep(random.uniform(0.5, 1.0))

    pyautogui.click()
    time.sleep(random.uniform(0.8, 1.5))   # 等待輸入框獲得焦點

    # 複製 JSON 到剪貼板
    copy_to_clipboard(word_json)
    time.sleep(random.uniform(0.42, 0.88))

    # 使用 Ctrl + V 快速貼上（推薦方式）
    print("📝 貼上 JSON 內容 (Ctrl + V)...")
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(random_delay(0.8))

    # ====================== 執行送出 (Ctrl + Enter) ======================
    print("⌨️ 執行送出 (Ctrl + Enter)...")
    pyautogui.hotkey('ctrl', 'enter')

    # 送出後的冷卻時間要跑大概40 秒 (random + - 3秒)
    cool_down_time = random_delay(40)
    print(f"⏳ 冷卻中... 等待 {cool_down_time:.2f} 秒")
    time.sleep(cool_down_time)


# ================== 你要的新功能：滾輪往下 3000 ==================
    pyautogui.moveTo(content_box_pos[0], content_box_pos[1], duration=0.9)

    print(f"🖱️ 開始往下滾動約 {abs(scroll_amount)} 單位...")

    # 分段滾動（更穩定）
    step_size = scroll_amount // scroll_steps
    for i in range(scroll_steps):
        pyautogui.scroll(step_size)
        time.sleep(random.uniform(0.15, 0.35))   # 每次小停頓，避免太快

    # 如果剩餘沒滾完，再補一次
    remaining = scroll_amount - (step_size * scroll_steps)
    if remaining != 0:
        pyautogui.scroll(remaining)

    print("✅ 滾輪往下滾動完成")



    # 移動到 740 310 download
    download_pos = (740, 310)
    print(f"🖱️ 移動到下載按鈕 {download_pos}")
    pyautogui.moveTo(download_pos[0], download_pos[1], duration=0.6)
    time.sleep(random.uniform(0.5, 1.2))

    # 點擊下載按鈕
    print("🖱️ 點擊下載按鈕")
    pyautogui.click()
    time.sleep(random.uniform(1, 2))

    # 移動到 760 1100 確認下載
    confirm_pos = (760, 1100)
    print(f"🖱️ 移動到確認下載按鈕 {confirm_pos}")
    pyautogui.moveTo(confirm_pos[0], confirm_pos[1], duration=0.6)
    time.sleep(random.uniform(0.5, 1.2))

    # 點擊確認下載按鈕
    print("🖱️ 點擊確認下載")
    pyautogui.click()
    time.sleep(random_delay(1.5))

    # 更新 checkpoint
    checkpoint_file.write_text(str(end_index))
    print(f"✅ 本批次完成！已更新 checkpoint 至第 {end_index} 行")

    # 如果不是最後一個循環，則休息 2 秒後繼續
    if loop_count < loops:
        print(f"⏸️ 本個循環完成，休息 2 秒後繼續下一個循環...")
        time.sleep(2)
    else:
        print(f"✅ 全部 {loops} 個循環已完成！")

print("\n🎉 所有自動化流程已完成！")