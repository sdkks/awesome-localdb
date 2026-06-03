# Tantivy

> **Category:** Search | **License:** MIT | **Stars:** ~13,000

## Overview

Tantivy is a full-text search engine library written in Rust, inspired by Apache Lucene. It provides everything you need to build a search index: inverted indexing, BM25 relevance scoring, configurable tokenization, fuzzy search, and faceted aggregation. Tantivy compiles to a single library with zero external dependencies and persists indexes to disk using a Lucene-like segment-based architecture. If you need fast, relevance-ranked full-text search embedded directly in your Rust application, Tantivy is the standard choice.

## Quick Start

### Rust

```rust
// Cargo.toml: tantivy = "0.22"
use tantivy::collector::TopDocs;
use tantivy::query::QueryParser;
use tantivy::schema::*;
use tantivy::{doc, Index, IndexWriter, ReloadPolicy, TantivyDocument};

fn main() -> tantivy::Result<()> {
    // Define schema
    let mut schema_builder = Schema::builder();
    let title = schema_builder.add_text_field("title", TEXT | STORED);
    let body = schema_builder.add_text_field("body", TEXT);
    let schema = schema_builder.build();

    // Create an in-memory index (or use create_in_dir for disk persistence)
    let index = Index::create_in_ram(schema);

    // Index documents
    let mut writer: IndexWriter = index.writer(50_000_000)?;
    writer.add_document(doc!(
        title => "The Old Man and the Sea",
        body => "He was an old man who fished alone in a skiff..."
    ))?;
    writer.add_document(doc!(
        title => "Moby-Dick",
        body => "Call me Ishmael. Some years ago..."
    ))?;
    writer.commit()?;

    // Search
    let reader = index.reader_builder()
        .reload_policy(ReloadPolicy::Manual)
        .try_into()?;
    reader.reload()?;
    let searcher = reader.searcher();
    let query_parser = QueryParser::for_index(&index, vec![title, body]);
    let query = query_parser.parse_query("old man")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;

    for (_score, doc_address) in top_docs {
        let retrieved = searcher.doc::<TantivyDocument>(doc_address)?;
        println!("{}", retrieved.to_json(&schema));
    }
    Ok(())
}
```

## On-Disk Format

Inverted Index Segments (multi-file, Lucene-like segment architecture)

## Core Strengths

- Lucene-equivalent full-text search with BM25 relevance scoring -- delivers production-grade search quality
- Zero external dependencies -- pure Rust, compiles to a single library without C/C++ linkage
- Segment-based architecture with lock-free concurrent reads -- multiple readers can search while a writer indexes
- Pluggable tokenizers with built-in options for simple, raw, whitespace, N-gram, and regex tokenization
- Fuzzy search, phrase queries, range queries, and boolean combinations give you full control over query execution
- Faceted search and aggregation support for building search UIs with drill-down filters

## Best Use Cases

1. **Full-text search over local document collections** -- Index markdown files, code repositories, or JSON documents with relevance-ranked retrieval.
2. **Building a search engine for a static site or documentation generator** -- Tantivy powers the search backend for tools that need local, fast, serverless search.
3. **In-app search for CLI tools and desktop applications** -- Embed search directly into your binary with no external service dependency.
4. **Embedding search into a Rust-based data pipeline or ETL tool** -- Add search indexing as a step in your data processing pipeline.
5. **Local knowledge base and personal wiki search** -- Build personal search engines over notes, bookmarks, and reference material.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Rust | [`recipe_search_index.rs`](rust/src/bin/recipe_search_index.rs) | Create an index from recipe data with structured fields |
| Rust | [`recipe_search_query.rs`](rust/src/bin/recipe_search_query.rs) | Search the index with BM25-ranked queries and display results |

## Limitations & Caveats

- Tantivy's built-in query parser is not designed for end-user consumption -- error messages are developer-oriented. For user-facing search, wrap the parser with friendlier error handling.
- Indexing is single-writer. Only one `IndexWriter` can exist per index at a time. If you need concurrent writes, batch them through a single writer.
- The on-disk format is not stable across major versions. Plan for re-indexing when upgrading Tantivy.
- Python bindings (`tantivy-py`) are available but maintained separately from the core library.

## Further Reading

- [Official Documentation](https://docs.rs/tantivy/)
- [Source Repository](https://github.com/quickwit-oss/tantivy)
