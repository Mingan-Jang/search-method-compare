# Search Methodology 工具包

一套完整的中文字典轉換和清洗工具。

## 📋 工具說明

### 01_convert.py
**功能**：使用本地 OpenCC 將簡體中文轉換為台灣正體中文
- **輸入**：`dict.txt`（簡體中文）
- **輸出**：`dict_tw_temp.txt`（台灣正體）
- **優點**：離線運行，無需 API Key，速度快

```bash
python 01_convert.py
```

### 02_clean-noise.py
**功能**：使用 Google Gemini AI 清洗字典資料
- **輸入**：`dict_tw_temp.txt`（轉換後的資料）
- **輸出**：`dict_cleaned.txt`（清潔的資料）
- **自動清洗**：
  - 移除重複項目
  - 刪除非中文內容
  - 清除特殊符號和亂碼
  - 整理格式

```bash
python 02_clean-noise.py
```

## 🚀 快速開始

### 1️⃣ 安裝依賴

```bash
pip install -r requirements.txt
```

### 2️⃣ 設定 Google API Key

#### 方案 A：使用 `.env` 檔案（推薦）

1. 複製 `.env.example`：
   ```bash
   cp .env.example .env
   ```

2. 在 `.env` 中填入你的 API Key：
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

3. 保確 `.env` 在 `.gitignore` 中（已預設配置）

#### 方案 B：設定系統環境變數

**Windows (PowerShell)**：
```powershell
$env:GOOGLE_API_KEY="your_api_key_here"
```

**Linux/Mac (Bash)**：
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 3️⃣ 取得 API Key

1. 訪問 [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. 點擊「Create API Key」
3. 選擇或建立一個專案
4. 複製生成的 API Key

### 4️⃣ 執行工具

```bash
# 第一步：轉換簡體 -> 台灣正體
python 01_convert.py

# 第二步：AI 清洗資料
python 02_clean-noise.py
```

## 📁 檔案結構

```
externals/
├── 01_convert.py          # 本地 OpenCC 轉換
├── 02_clean-noise.py           # AI 清洗工具
├── requirements.txt       # 依賴列表
├── .env.example          # 環境變數範本
├── .env                  # ⚠️ 本地密鑰（不上傳）
├── .gitignore            # Git 忽略規則
├── dict.txt              # 輸入：原始簡體字典
├── dict_tw_temp.txt      # 中間：轉換後的台灣正體
└── dict_cleaned.txt      # 輸出：最終清洗資料
```

## 🔐 安全最佳實踐

### ✅ 必做事項

1. **絕不上傳密鑰**：確保 `.env` 在 `.gitignore` 中
2. **使用環境變數**：代碼中始終用 `os.getenv()` 讀取密鑰
3. **定期更換密鑰**：如果意外暴露，立即吊銷並重新生成

### 📋 檢查清單

```bash
# 確認 .gitignore 包含 .env
cat .gitignore | grep .env

# 確認代碼沒有硬編碼密鑰
grep -r "AIzaSy" .
```

### 🚨 如果密鑰被暴露

1. [撤銷舊密鑰](https://console.cloud.google.com/apis/credentials)
2. 生成新密鑰
3. 更新本地 `.env`
4. 檢查 Git 歷史中是否有密鑰（如有需清理）

## 📊 成本估算（Google Gemini API）

- **模型**：Gemini 2.0 Flash（最便宜的模型）
- **定價**：輸入 $0.075/100 萬個 token，輸出 $0.30/100 萬個 token
- **範例**：清洗 10,000 行資料 ≈ 0.001-0.01 USD

[查看最新定價](https://ai.google.dev/pricing)

## 🛠️ 故障排除

### 問題：`ModuleNotFoundError: No module named 'opencc'`
**解決**：執行 `pip install -r requirements.txt`

### 問題：`400 Bad Request - Invalid API Key`
**解決**：檢查 `.env` 中的 API Key 是否正確

### 問題：API 超時（timeout）
**解決**：檢查網路連線，或減少 `batch_size` 參數

### 問題：輸出檔案為空
**解決**：檢查輸入檔案是否存在且包含資料

## 📝 進階用法

### 自訂批次大小
編輯 `02_clean-noise.py` 的 `batch_size` 參數（預設：50 行）
```python
success = clean_with_ai(input_file, output_file, batch_size=100)
```

### 使用不同的 Gemini 模型
編輯 `model_name` 參數：
```python
model = genai.GenerativeModel(model_name='gemini-1.5-pro')
```

## 📚 相關資源

- [OpenCC 文檔](https://github.com/BYVoid/OpenCC)
- [Google Generative AI Python 文檔](https://github.com/google/generative-ai-python)
- [Gemini API 定價](https://ai.google.dev/pricing)

## 📄 授權

MIT License（自由使用和修改）

---

**提示**：首次執行時，建議先用小規模測試檔案驗證設定是否正確。
