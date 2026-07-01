# FieldOps-AI

**技術検証 — RAG ハイブリッド検索 + Domain-ML Fusion**

製造現場の課題を RAG と Domain-ML Fusion でどう扱えるかを検証する個人プロジェクトです。すべてモック（合成）データで構築・検証しており、特定の企業・製品の実データやパラメータは使用していません。

[English version](README.md)

![Python](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-19-61DAFB)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Oracle](https://img.shields.io/badge/Oracle-26ai-F80000)

### [▶ ライブデモ（GitHub Pages）](https://seunghwan-dev.github.io/fieldops-ai/)

DEMOモード — Docker不要。ML Only ↔ Fusionを切り替えて違いを確認できます。

---

## Before / After

<p align="center">
  <img src="docs/images/before-after.svg" alt="Before/After" width="100%"/>
</p>

> ML単独では数値だけ。警告も根拠もなし。Fusionはドメイン知識で補正し、出典を提示します。すべての出力は人間の承認を経てから実行されます。

---

## アーキテクチャ

<p align="center">
  <img src="docs/images/architecture.svg" alt="FieldOps-AI Architecture" width="100%"/>
</p>

> クラウドVLMで論文を取り込み、抽出精度を最大化。Track Aはナレッジベースを検索、Track Bは実験データ（CSV）で学習したMLモデルを使用。予測と推論はすべてローカルGPUで完結。データの外部流出なし、APIコストゼロ。

---

## 機能

<p align="center">
  <img src="docs/images/features.svg" alt="Features" width="100%"/>
</p>

> コア機能は3つ。Domain-ML Fusionが根拠を示して予測を補正し、RAGがナレッジベースから即座に回答、VLMが論文PDFから構造化データを抽出します。

---

## 技術スタック

| コンポーネント | 技術 | 選定理由 |
|---------------|------|----------|
| LLM | Qwen 2.5 7B（Ollama、ローカル） | 外部API呼び出しなし、データ主権 |
| VLM | GPT-4o Vision（Azure OpenAI） | テーブル・図の抽出精度が最高 |
| データベース | Oracle AI Database 26ai | Vector + BM25ハイブリッドを単一DBで実現 |
| Embedding | multilingual-e5-large（1024次元） | 日英韓の多言語対応 |
| ML | RandomForest + SHAP | 解釈可能な予測 + XAI |
| フロントエンド | React 19 + TypeScript + Tailwind | EN/JA二言語UI |
| Fusion | LLM Layer + Rule-based Safety | 柔軟性と絶対性を両立する二層構造 |

---

## 主要な設計判断

### 1. 装置A vs B：異なるMLアプローチ

<p align="center">
  <img src="docs/images/equipment-a-vs-b.svg" alt="Equipment A vs B" width="100%"/>
</p>

> 装置Aは物理式が存在しないため、MLが実験報告書から直接学習。装置BにはBond's Lawがあるが、特定のRPM範囲外では誤差が出る。その差分をMLが補正します。

### 2. Fusion：LLMの柔軟性 + Ruleの絶対性

<p align="center">
  <img src="docs/images/fusion-dual-layer.svg" alt="Fusion Dual-Layer" width="100%"/>
</p>

> Layer 1（LLM）は柔軟に根拠を統合し補正を提案。Layer 2（Rule）はハードコードされた安全ルールで、他のすべての判断に優先します。二層構造で安全性に妥協なし。

### 3. MDSK-RAG Dual-Source Collection

[MDSK-RAGパターン（ACS JCIM）](https://pubs.acs.org/doi/10.1021/acs.jcim.5c01941)を参考に、ナレッジを2つのテーブルに物理的に分離しています。

<p align="center">
  <img src="docs/images/mdsk-rag.svg" alt="MDSK-RAG Dual-Source" width="100%"/>
</p>

> 単一テーブルではテキスト知識と数値データが混在し、検索精度が低下。文献と定量データを物理的に分離し、それぞれに最適なインデックスを構築。実運用では、同じパターンを機密データと公開データの分離にも応用できます。

### 4. ハイブリッド・チャンキングと MDSK-RAG ルーティング

PDF コンテンツは固定長ではなく **コンテンツ種別ごと** に分割する：

- **テキスト** — 段落境界で分割、上限 400 トークン（約 1,600 文字）、オーバーラップなし。見出しは `section_title` メタデータに保持。
- **表** — 行レベルで分割（ヘッダ + データ1行 = 1チャンク）、`Table {id} | Header1: Value1 | Header2: Value2 | ...` 形式。各行が独立して検索可能。
- **図** — VLM 生成の `semantic_summary` と `key_data_points` を結合して 1チャンク。図キャプションは `section_title` に格納。

チャンクは種別により **2 つの Oracle テーブルに物理分離** される（MDSK-RAG）：

| chunk_type | テーブル | 用途 |
|------------|---------|------|
| `text`, `figure` | `LITERATURE_CHUNKS` | 説明的・概念的な検索 |
| `table_row` | `QUANTITATIVE_CHUNKS` | 数値・閾値検索 |

定性的な質問は文献テーブルへ、数値条件の質問（例：「discharge temp > 200°C」）は定量テーブルへとベクトル検索が向かう。両者はハイブリッド検索（vector + BM25 + RRF）パイプラインに統合される。

## ロードマップ

本リポジトリは技術検証であり、以下は設計済みの拡張項目（未実装）です。

- **クエリリライト** — 検索前にクエリを書き換え、曖昧な質問の再現率を改善
- **CI/CD 拡張** — 既存の secret-scan / Pages デプロイ workflow をテスト・ビルド自動化へ拡張
- **LLM トークン・コスト計測** — Ollama / Azure 横断のリクエスト単位トークン集計
- **メトリクス・ダッシュボード** — Prometheus + Grafana によるレイテンシ・検索品質・fusion confidence の可視化
- **TLS リバースプロキシ** — localhost 以外へのデプロイ向け HTTPS 終端
- **デプロイアーキテクチャ文書** — ローカル docker-compose を超えた本番トポロジ
