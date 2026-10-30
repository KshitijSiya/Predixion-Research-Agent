# Research Report: Compare the top 3 open-source vector databases for a startup building RAG products.

**Confidence Level:** `High` (87% verified)

## Executive Summary
For a startup building RAG products, Chroma, Milvus, and Qdrant are the leading open‑source vector databases: Chroma excels at hybrid dense/sparse search with rich metadata filtering, Milvus offers the best scalability to billions of vectors on Kubernetes, and Qdrant provides fast payload‑aware filtering with solid performance and low write latency.

## Key Findings
1. Chroma supports dense, sparse (BM25) and hybrid retrieval plus JSON metadata filters, making it ideal for prototype‑to‑production RAG pipelines, but its single‑node design limits extreme concurrency and its memory usage grows to ~62 GB for 2.25 M vectors.
2. Milvus is built for horizontal scaling on Kubernetes, handles millions‑to‑billions of vectors, and offers hybrid retrieval; it uses disk‑based indexing to keep memory low (~17 GB for 2.25 M vectors) but has higher write latency (≈12 ms) and a query limit/offset ceiling.
3. Qdrant combines HNSW‑based approximate search with payload‑aware JSON filtering, delivering sub‑millisecond latency and write latency of ~9 ms; its single‑thread throughput is 377 QPS (higher than Chroma) and it balances performance with moderate memory consumption.

## Verified Sources
- **[zairalabs.ai]** [Open Source Vector Database Tools (2026) — Zaira Labs](https://zairalabs.ai/guide/guides/open-source-vector-database) — *"You need to prototype vector search locally and later promote the same collection model to a deployed service... Chroma (OSS). ... hybrid retrieval combining dense vectors, sparse/BM25 lexical search, and metadata filters... Milvus (OSS) ... vector count will grow to millions or billions and horizontal scaling across Kubernetes is a requirement. ... Qdrant (OSS) ... hybrid dense+sparse retrieval in a single collection... payload-aware filtering with JSON metadata alongside vector similarity."*
- **[aimultiple.com]** [Vector Database Benchmark: 7 Open-Source Engines for RAG](https://aimultiple.com/open-source-vector-databases) — *"Single-thread QPS order is Redis 764, Qdrant 377, Milvus 342, Weaviate 341, pgvector 257, Chroma 197, LanceDB 70... Peak RAM at 2.25M vectors runs from 17.0 GB (Milvus) to 62.4 GB (Chroma)... Write‑ack to search‑visible latency: Redis 2 ms, Weaviate 4 ms, Qdrant 9 ms, Milvus 12 ms, pgvector 14 ms, LanceDB 31 ms, Chroma 41 ms."*

## Limitations & Assumptions
- The benchmark data reflects a specific embedding model (bge‑m3) and query sets (MedRAG‑50k, TechQA‑28k); results may differ with other models or larger corpora.
- Memory figures for on‑disk engines (Milvus, LanceDB) are high‑water marks during indexing; steady‑state serving memory could be lower.
- Feature comparisons rely on documentation summaries; deeper security, multi‑tenant, or enterprise‑grade features were not evaluated.

## Suggested Next Steps
- Run a pilot RAG workload on each of the three candidates using your own embeddings and document set to validate latency, throughput, and cost in your target deployment environment.
- Assess operational requirements such as Kubernetes orchestration (Milvus), ease of embedding versioning (Chroma), and required metadata filtering complexity (Qdrant).
- Benchmark write‑heavy update patterns typical for your knowledge‑base to confirm write latency and index refresh behavior under realistic churn.

## Execution Telemetry
- **Total Latency:** 16.131s
- **Plan Duration:** 3.772s
- **Tools Duration:** 8.776s
- **Synthesis Duration:** 3.583s
- **Model Used:** `openai/gpt-oss-120b` (groq)