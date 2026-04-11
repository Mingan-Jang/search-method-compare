# Search-Method-Compare API 🔍

[![Java](https://img.shields.io/badge/Java-17%2B-orange)](https://突出Java背景)
[![Vue](https://img.shields.io/badge/Vue-3.x-brightgreen)](https://突出Vue背景)
[![Postgres](https://img.shields.io/badge/Postgres-FTS-blue)](https://DB實作)
[![WASM](https://img.shields.io/badge/WebAssembly-Jieba-purple)](https://前端實作)

> **這不是一個單純的搜尋功能，而是一個針對「檢索架構選型」的技術實驗平台。**

本專案旨在探討在不同數據規模與業務場景下，三種主流檢索策略的效能表現、成本代價與實作複雜度。透過統一的介面，實現了對 **Elasticsearch**、**PostgreSQL Full-Text Search** 以及 **Frontend WebAssembly** 的橫向比對。

## 🏗 核心架構 (Experimental Methodology)

系統將數據檢索切分為三種維度進行實驗：

| 方法 (Methodology) | 技術棧 (Tech Stack) | 實驗核心                    | 適用場景                           |
| :----------------- | :------------------ | :-------------------------- | :--------------------------------- |
| **Service-Side**   | **Elasticsearch**   | 分散式反向索引、Rest Client | 大數據量、複雜權重搜尋             |
| **Database-Side**  | **PostgreSQL FTS**  | GIN Index、tsvector         | 中小型系統、強一致性需求           |
| **Client-Side**    | **Vue 3 + WASM**    | Jieba-WASM、Web Worker      | 極低延遲、離線檢索、減輕伺服器負擔 |

## Piror Art

https://github.com/messense/jieba-rs
https://github.com/fengkx/jieba-wasm
