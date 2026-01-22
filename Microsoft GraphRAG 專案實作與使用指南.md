# Microsoft GraphRAG 專案實作與使用指南

## 摘要

**Microsoft GraphRAG**（Graph + Retrieval Augmented Generation，圖譜增強檢索生成）是微軟研究院開發的一項創新技術，旨在透過結合**知識圖譜**、**網絡分析**與**大型語言模型（LLM）**的力量，來豐富對非結構化文本數據集的理解與查詢能力 [1]。傳統的 RAG 系統主要依賴向量搜索，難以處理需要跨文檔聚合或複雜關係推理的查詢。GraphRAG 透過將文本數據轉化為結構化的知識圖譜，並利用圖譜結構進行**社區檢測**與**摘要生成**，顯著提升了 LLM 在處理複雜、高層次問題時的準確性與洞察力 [2]。

本指南將詳細介紹 GraphRAG 的核心原理、專案實作流程、關鍵配置以及如何利用其強大的查詢機制。

## 1. 核心原理與架構

GraphRAG 的核心在於其多階段的**索引管道（Indexing Pipeline）**，它將原始文本數據逐步轉化為可供 LLM 進行複雜推理的結構化資產 [2]。

### 1.1 索引管道階段

GraphRAG 的索引流程是模組化的，主要步驟如下表所示 [2]：

| 階段名稱 | 目的與功能 | 關鍵輸出資產 |
| :--- | :--- | :--- |
| **文本分塊 (Chunking)** | 將輸入文檔切分為大小適中的文本塊，為後續處理做準備。 | 文本塊 (Chunks) |
| **實體與關係提取 (Extraction)** | 使用 LLM 識別文本塊中的實體（如人、地、事）及其相互關係。 | 實體 (Entities)、關係 (Relationships) |
| **圖譜構建 (Graph Construction)** | 將提取的實體和關係轉化為知識圖譜結構。 | 知識圖譜 (Knowledge Graph) |
| **社區檢測 (Community Detection)** | 使用 Leiden 等算法對圖譜進行層次化聚類，將相關實體分組。 | 社區層級結構 (Community Hierarchy) |
| **社區摘要 (Summarization)** | 為每個檢測到的社區生成高層次的摘要報告，捕捉該社區的主題與核心內容。 | 社區報告 (Community Reports) |
| **向量嵌入 (Embedding)** | 為實體、關係和文本塊生成向量表示，用於高效檢索。 | 向量索引 (Vector Index) |

### 1.2 查詢機制

GraphRAG 提供了兩種主要的查詢方法，以應對不同複雜度的用戶問題 [3]：

| 查詢方法 | 適用場景 | 核心原理 |
| :--- | :--- | :--- |
| **Global Search (全局搜索)** | 總結性問題、主題分析、跨文檔聚合（例如：「數據集中的主要趨勢是什麼？」）。 | 採用 **Map-Reduce** 模式。Map 階段並行處理相關社區摘要並評分，Reduce 階段匯總高分答案，提供全局視角。 |
| **Local Search (本地搜索)** | 針對特定實體的具體問題、細節查詢（例如：「Scrooge 的主要關係有哪些？」）。 | 結合**向量搜索**（尋找相關實體）和**圖遍歷**（尋找關聯關係和文本塊），將精確的上下文傳遞給 LLM。 |

## 2. 專案實作流程

實作一個 GraphRAG 專案主要透過其命令行介面（CLI）工具 `graphrag` 進行 [4]。

### 2.1 環境準備與安裝

GraphRAG 是一個 Python 庫，建議使用 Python 3.10-3.12 版本 [1]。

1.  **安裝 GraphRAG 庫**:
    ```bash
    pip install graphrag
    ```

2.  **準備輸入數據**:
    將您的非結構化文本文件（如 `.txt`, `.pdf`, `.md` 等）放入一個專案目錄下的 `input` 資料夾中。

### 2.2 專案初始化與配置

專案初始化會創建必要的配置檔案，以便您連接 LLM 服務並調整管道參數。

1.  **初始化專案**:
    假設您的專案目錄為 `./my_graphrag_project`：
    ```bash
    graphrag init --root ./my_graphrag_project
    ```
    此命令會在專案根目錄下生成兩個關鍵檔案：
    *   `.env`: 用於儲存敏感資訊，例如 `GRAPHRAG_API_KEY`。
    *   `settings.yaml`: 包含所有管道配置的 YAML 檔案。

2.  **配置 LLM 服務**:
    您必須在 `.env` 檔案中設定您的 LLM API 金鑰。GraphRAG 原生支持 OpenAI 和 Azure OpenAI [1]。

    *   **OpenAI**:
        ```
        GRAPHRAG_API_KEY=<您的 OpenAI API Key>
        ```
    *   **Azure OpenAI**:
        除了 API Key，您還需要在 `settings.yaml` 中配置 `api_base`、`api_version` 和 `deployment_name` 等參數，並將模型類型設定為 `azure_openai_chat` 或 `azure_openai_embedding`。

### 2.3 數據索引（建立知識圖譜）

這是專案的核心步驟，它將您的原始數據轉化為知識圖譜。

1.  **運行索引管道**:
    ```bash
    graphrag index --root ./my_graphrag_project
    ```
    此過程將執行 1.1 節中描述的所有階段。完成後，所有生成的資產（實體、關係、社區報告等）將以 Parquet 檔案格式儲存在 `./my_graphrag_project/output` 資料夾中 [4]。

### 2.4 提示詞調整（Prompt Tuning）

為了優化實體和關係的提取質量，GraphRAG 提供了提示詞調整功能。

1.  **自動調整提示詞 (Auto Tuning)**:
    強烈建議運行此命令，它會根據您的數據集自動生成最適合的實體提取提示，以提高準確性 [5]。
    ```bash
    graphrag prompt-tune --root ./my_graphrag_project
    ```
    生成的提示詞將儲存在 `./my_graphrag_project/prompts` 資料夾中。

## 3. 專案查詢與使用

一旦索引完成，您就可以使用 `query` 命令來查詢您的知識圖譜。

### 3.1 執行查詢

使用 `--method` 參數指定查詢類型（`global` 或 `local`），並使用 `--query` 參數傳入您的問題 [4]。

1.  **Global Search 範例（高層次問題）**:
    ```bash
    graphrag query \
      --root ./my_graphrag_project \
      --method global \
      --query "What are the top themes discussed in the documents?"
    ```

2.  **Local Search 範例（細節問題）**:
    ```bash
    graphrag query \
      --root ./my_graphrag_project \
      --method local \
      --query "Tell me more about the relationship between Entity A and Entity B."
    ```

### 3.2 查詢參數調整

您可以在查詢時調整一些關鍵參數以優化結果 [4]：

| 參數 | 說明 | 預設值 | 適用方法 |
| :--- | :--- | :--- | :--- |
| `--community-level` | 指定 Global Search 應從哪個層級的社區報告中提取上下文。數字越大，社區越小，報告越詳細。 | 2 | Global |
| `--response-type` | 描述您期望的回答格式（例如：'Single Sentence', 'List of 3-7 Points'）。 | Multiple Paragraphs | Global/Local |
| `--streaming` | 啟用流式輸出，即時顯示 LLM 的回答。 | False | Global/Local |

## 4. 總結與建議

GraphRAG 透過將 RAG 的檢索能力與知識圖譜的結構化推理相結合，提供了一個強大的解決方案，特別適用於處理複雜、敘事性強或需要跨文檔關係分析的數據集。

**建議**:
*   **從小處著手**: 由於 GraphRAG 會消耗大量的 LLM 資源，建議您先使用小型數據集和 `prompt-tune` 功能來優化您的提示詞，以確保提取質量，再進行大規模索引 [1]。
*   **利用可視化**: 官方文件提供了可視化指南，建議您使用相關工具（如 Jupyter Notebooks）來探索生成的知識圖譜，這有助於理解數據結構和調試索引結果 [1]。
*   **靈活運用查詢**: 根據您的問題性質，靈活切換 `global` 和 `local` 查詢方法，以獲得最精確和全面的答案。

---
## 參考資料

[1] [Welcome - GraphRAG](https://microsoft.github.io/graphrag/)
[2] [Indexing Overview - GraphRAG](https://microsoft.github.io/graphrag/indexing/overview/)
[3] [Query Overview - GraphRAG](https://microsoft.github.io/graphrag/query/overview/)
[4] [CLI Reference - GraphRAG](https://microsoft.github.io/graphrag/cli/)
[5] [Prompt Tuning Overview - GraphRAG](https://microsoft.github.io/graphrag/prompt_tuning/overview/)
