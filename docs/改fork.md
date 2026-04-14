````md
# jieba-wasm 加入 POS Tagger（詞性輸出）修改指南

本文件說明如何在 fork 的 `jieba-wasm` 中加入詞性（POS）輸出功能。


# 🎯 目標

讓前端可以使用：

```js
cut_with_pos("我在台北吃飯")
````

輸出：

```json
[
  { "word": "我", "tag": "r" },
  { "word": "在", "tag": "p" },
  { "word": "台北", "tag": "ns" },
  { "word": "吃飯", "tag": "v" }
]
```

---

# 🧱 架構理解

```
jieba-rs      → 已具備 Tagger（有詞性能力）
    ↓
jieba-wasm    → 需要 expose Tagger API（你要改這層）
    ↓
Frontend JS   → 呼叫 wasm function
```

---

# 🛠 Step 1：先確認現況（這個 fork 已有 `tag()`）

目前此 fork 的 `src/lib.rs` 已經有：

* `tag(sentence, hmm)`：回傳 `[{ word, tag }]`

所以實作目標可改成「新增 `cut_with_pos()` 別名 API」，避免破壞既有介面。

---

# 🛠 Step 2：新增 Token 結構（Rust）

在 wasm `lib.rs` 或相關檔案加入：

```rust
use serde::Serialize;

#[derive(Serialize)]
struct Token {
    word: String,
    tag: String,
}
```

---

# 🛠 Step 3：新增 POS API（核心功能）

```rust
#[wasm_bindgen]
pub fn cut_with_pos(text: &str, hmm: Option<bool>) -> Vec<JsValue> {
    // fork 最小改動：直接重用既有 tag() 行為
    tag(text, hmm)
}
```

---

# 🛠 Step 4：確認相依套件

Cargo.toml 確保：

```toml
wasm-bindgen = { version = "0.2.101", features = ["serde-serialize"] }
serde = { version = "1.0", features = ["derive"] }
serde-wasm-bindgen = "0.6.5"
```

---

# 🛠 Step 5：前端使用方式

```js
import init, { cut_with_pos } from "./pkg/jieba_wasm.js";

await init();

const result = cut_with_pos("我在台北吃飯");

console.log(result);
```

---

# ⚡ Step 6（可選優化）：維持單例，不要新增第二套分詞器

本 fork 目前已使用全域單例：

```rust
static JIEBA: LazyLock<Mutex<Jieba>> = LazyLock::new(|| Mutex::new(Jieba::new()));
```

`cut_with_pos()` 直接委派給 `tag()` 即可，不需要再建立 `Tagger::new()`。

---

# 🚀 Step 7（可選）：加「關鍵字過濾版本」

```rust
#[wasm_bindgen]
pub fn cut_keywords(text: &str) -> JsValue {
    let blacklist = ["u", "r", "p"];

    let result: Vec<String> = JIEBA.lock().unwrap()
        .tag(text)
        .into_iter()
        .filter(|(_, tag)| !blacklist.contains(&tag.as_str()))
        .map(|(w, _)| w.to_string())
        .collect();

    serde_wasm_bindgen::to_value(&result).unwrap()
}
```

---

# ⚠️ 常見問題

## 1. 沒有 `cut_with_pos`

→ 你可能只停在文件修改，尚未在 `src/lib.rs` 匯出該函式

## 2. wasm 編譯失敗

→ serde / wasm-bindgen 版本不對

## 3. 有分詞但沒詞性

→ 你可能呼叫了 `cut()`，請改呼叫 `tag()` 或 `cut_with_pos()`

---

# 🎯 最終結果

你會得到：

* 前端直接 POS 分詞
* 無需 Python
* 全 WASM 執行
* 可做關鍵字過濾 / NLP 前處理

---

# 🧭 建議架構（最佳實務）

👉 保留原本 `cut()`
👉 新增 `cut_with_pos()`
👉 不破壞 upstream API

---

# 🔁 Fork 維護策略（重點）

因為這是 fork，建議把「功能可用」和「未來可同步 upstream」一起設計：

1. 變更原則：只新增、少覆寫

* 儘量採用「新增函式」而非修改既有函式。
* 不改原有輸出格式，避免影響現有呼叫端。
* 若要擴充參數，優先做新 API（例如 `cut_with_pos_options`），不要直接改 `cut` 行為。

2. 變更範圍最小化

* 優先集中在 `src/lib.rs` 與必要的 `Cargo.toml` feature。
* 避免在多個檔案分散修改同一件事，減少 rebase 衝突面。
* 可把 POS 相關程式拆到獨立模組（例如 `src/pos.rs`）再由 `lib.rs` 匯出。

3. API 相容策略

* 保留舊 API：`cut()`、`cut_all()`、`cut_for_search()`。
* 新增 API：`cut_with_pos()`。
* 若要關鍵字過濾，建議額外新增 `cut_keywords()`，不要混入 `cut_with_pos()` 預設行為。

4. 用 feature flag 管理風險

* 將 POS 能力放在可控 feature（例如 `pos`）下。
* 預設行為保持與 upstream 一致，必要時再開啟 `pos`。
* 這樣可在同步 upstream 時降低行為差異。

5. Git 工作流（建議）

* 每一個能力用一個獨立 commit（例如「add pos api」「add keyword filter」）。
* 不把格式化、重命名、功能變更混在同一 commit。
* 保留 upstream remote，固定流程同步：

```bash
git remote add upstream <original-repo-url>
git fetch upstream
git checkout main
git rebase upstream/main
```

6. 測試與驗證門檻

至少保留兩組測試：

* 相容測試：既有 `cut()` 輸出不變。
* 新功能測試：`cut_with_pos("我在台北吃飯")` 具備詞性輸出欄位。

---

# ✅ 完成
