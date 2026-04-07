# Architecture

## Supported Runtime

The repository now centers on one runtime:

`PortfolioAgent`

That SDK owns:
- ingestion
- embedding
- indexing
- querying

## Flow

```text
File / repo / website / text
        |
     Ingestor
        |
      Chunker
        |
     Embedder
        |
   FAISSVectorStore
        |
      Query
        |
   RouterAgent
        |
 RetrieverAgent
        |
 RerankerAgent
        |
  PersonaAgent
        |
 MemoryManager
        |
    Response
```

## Design Notes

- The supported package surface is the SDK, not the old graph-first entrypoint.
- The FastAPI app is a thin wrapper over the SDK rather than a separate orchestration layer.
- Legacy placeholder modules have been isolated under explicit legacy namespaces and are not part of the documented public contract.
