import os
import shutil
from opencc import OpenCC

def convert_and_deploy():
    # --- 路徑設定 ---
    # 你的原始工具路徑
    base_plugin_dir = r".\elasticsearch-analysis-ik-8.10.2"
    config_path = os.path.join(base_plugin_dir, "config")
    backup_path = os.path.join(base_plugin_dir, "config_backup")
    
    # 你的 Docker 目錄目標路徑
    docker_es_plugin_ik = r"..\docker\es-plugins\ik"

    # 1. 備份 config (如果不存在備份才執行)
    if os.path.exists(config_path):
        if not os.path.exists(backup_path):
            print(f"正在備份 config 到 {backup_path}...")
            shutil.copytree(config_path, backup_path)
        else:
            print("備份資料夾已存在，跳過備份步驟。")
    else:
        print("找不到 config 資料夾，請確認路徑！")
        return

    # 2. 進行 OpenCC 轉換 (針對原本的 config 資料夾)
    cc = OpenCC('s2twp')
    files = [f for f in os.listdir(config_path) if f.endswith('.dic')]
    
    print(f"找到 {len(files)} 個 .dic 檔案，開始轉換為繁體中文...")
    for file_name in files:
        file_path = os.path.join(config_path, file_name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            converted_lines = [cc.convert(line) for line in lines]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(converted_lines)
            print(f"成功處理: {file_name}")
        except Exception as e:
            print(f"處理 {file_name} 時發生錯誤: {e}")

    # 3. 轉移至 Docker 的 es-plugins/ik
    print(f"\n準備轉移插件至: {docker_es_plugin_ik}")
    
    # 如果目標資料夾已存在，先刪除舊的以確保乾淨安裝
    if os.path.exists(docker_es_plugin_ik):
        print("目標 ik 資料夾已存在，正在覆蓋...")
        shutil.rmtree(docker_es_plugin_ik)
    
    # 建立目標父目錄 (es-plugins)
    os.makedirs(os.path.dirname(docker_es_plugin_ik), exist_ok=True)
    
    # 複製整個插件目錄內容到 docker/es-plugins/ik
    # 注意：我們是複製 base_plugin_dir 裡面的「內容」
    shutil.copytree(base_plugin_dir, docker_es_plugin_ik)
    print(f"轉移完成！請記得執行 'docker-compose restart elasticsearch' 重啟服務。")

if __name__ == "__main__":
    convert_and_deploy()