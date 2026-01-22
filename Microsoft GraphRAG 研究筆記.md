# Microsoft GraphRAG 研究筆記

## 1. 核心概念
GraphRAG (Graphs + Retrieval Augmented Generation) 是由 Microsoft Research 開發的一種技術，旨在通過結合文本提取、網絡分析和 LLM 來豐富對文本數據集的理解。

## 2. 索引流程 (Indexing Pipeline)
GraphRAG 的索引流程是模組化的，主要步驟包括：
1. **文本分塊 (Text Chunking)**: 將輸入文檔切分為可處理的塊。
2. **實體與關係提取 (Entity & Relation Extraction)**: 使用 LLM 識別文本中的實體（如人、地、事）及其相互關係。
3. **圖譜構建 (Graph Construction)**: 將提取的實體和關係轉化為圖結構。
4. **社區檢測 (Community Detection)**: 使用 Leiden 算法對圖進行層次化聚類。
5. **社區摘要 (Community Summarization)**: 為每個檢測到的社區生成摘要報告，這是全局搜索的核心。
6. **聲明提取 (Claim Extraction)**:（可選）提取關於實體的具體事實聲明。
7. **向量嵌入 (Embedding)**: 為實體、關係和文本塊生成向量，用於檢索。

## 3. 查詢機制 (Query Mechanisms)
- **Global Search (全局搜索)**:
    - **原理**: 採用 Map-Reduce 方式。Map 階段並行處理各個社區摘要並評分，Reduce 階段匯總高分答案。
    - **適用場景**: 總結性問題、主題分析、跨文檔聚合。
- **Local Search (本地搜索)**:
    - **原理**: 結合向量搜索（尋找相關實體）和圖遍歷（尋找關聯關係和文本塊）。
    - **適用場景**: 針對特定實體的具體問題、細節查詢。
- **DRIFT Search**: 一種結合了全局和本地優點的新型搜索方式（最新版本引入）。

## 4. 快速入門步驟
1. **安裝**: `pip install graphrag`
2. **初始化**: `graphrag init --root ./project_dir`
3. **配置**: 修改 `.env` (API Key) 和 `settings.yaml`。
4. **索引**: `graphrag index --root ./project_dir`
5. **查詢**: `graphrag query --root ./project_dir --method [global|local] --query "your question"`

## 5. 配置與優化
- **settings.yaml**: 控制 LLM 模型選擇、API Base、分塊大小、社區層級等。
- **Prompt Tuning**:
    - **Auto Tuning**: 使用 `graphrag prompt-tune` 根據你的數據自動生成最適合的實體提取提示。
    - **Manual Tuning**: 手動修改 `prompts/` 目錄下的文件。
- **數據輸出**: 索引結果存儲在 `output/` 目錄下的 Parquet 文件中，可以使用 Pandas 或 DuckDB 查看。
- **LLM 支持**: 原生支持 OpenAI 和 Azure OpenAI，通過配置 `api_base` 也可以支持相容的本地模型（如 Ollama, vLLM）。
