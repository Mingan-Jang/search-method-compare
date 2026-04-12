import os
import sys
import urllib.request
from opencc import OpenCC

def download_dict(url, save_path):
    """從指定 URL 下載字典檔"""
    print(f"🌐 找不到本地檔案，嘗試從網路下載...")
    try:
        # 設定 User-Agent 避免某些伺服器封鎖爬蟲
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req) as response, open(save_path, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        print(f"📥 下載成功：{save_path}")
        return True
    except Exception as e:
        print(f"❌ 下載失敗: {e}")
        return False

def main():
    # 強制使用腳本所在的目錄
    base_path = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_path, 'dict.txt')
    output_file = os.path.join(base_path, 'dict_tw_temp.txt')
    remote_url = "https://github.com/fxsjy/jieba/raw/master/extra_dict/dict.txt.big"
    
    print(f"--- 環境檢查 ---")
    print(f"目前執行位置: {os.getcwd()}")
    
    # 檢查檔案，若不存在則下載
    if not os.path.exists(input_file):
        success = download_dict(remote_url, input_file)
        if not success:
            print(f"❌ 錯誤：無法取得資料來源，請檢查網路連線。")
            return

    # s2twp: 簡體 -> 台灣正體
    cc = OpenCC('s2twp')

    print(f"🚀 開始本地 OpenCC 轉換...")
    
    count = 0
    try:
        # 使用 utf-8 讀取並轉換
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                clean_line = line.strip()
                if clean_line:
                    converted = cc.convert(clean_line)
                    f_out.write(converted + '\n')
                    count += 1
        
        print(f"✅ 轉換完成！共處理 {count} 筆資料。")
        print(f"輸出檔案路徑：{output_file}")
        
    except Exception as e:
        print(f"❌ 轉換過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()