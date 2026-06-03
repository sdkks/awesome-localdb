# Bleve

> **Category:** Search | **License:** Apache-2.0 | **Stars:** ~10,000

## Overview

Bleve is a modern full-text search and indexing library for Go. It supports text, numeric, geo-spatial, and vector indexing with a simple, idiomatic Go API. Bleve runs embedded in-process with zero external dependencies, using BoltDB as the default persistent storage backend. Its rich query DSL supports boolean, phrase, fuzzy, term range, geo distance, and prefix queries, with TF-IDF or BM25 scoring, result highlighting, and faceted search across 30+ languages.

## Quick Start

### Go

```go
package main

import (
	"fmt"
	"log"

	"github.com/blevesearch/bleve/v2"
)

func main() {
	// Create or open an index
	index, err := bleve.New("recipes.bleve", bleve.NewIndexMapping())
	if err != nil {
		log.Fatal(err)
	}
	defer index.Close()

	// Index a document
	recipe := map[string]interface{}{
		"name":    "Classic Margherita Pizza",
		"cuisine": "Italian",
		"ingredients": []string{
			"pizza dough", "tomato sauce",
			"fresh mozzarella", "basil", "olive oil",
		},
	}
	index.Index("1", recipe)

	// Search
	query := bleve.NewQueryStringQuery("mozzarella")
	searchRequest := bleve.NewSearchRequest(query)
	searchResult, _ := index.Search(searchRequest)

	fmt.Printf("Found %d results\n", searchResult.Total)
	for _, hit := range searchResult.Hits {
		fmt.Printf("  %s (score: %.2f)\n", hit.ID, hit.Score)
	}
}
```

## On-Disk Format

BoltDB-backed inverted index (B+Tree memory-mapped single file)

## Core Strengths

- Simple top-level API -- index any Go struct without boilerplate
- Full-text search with TF-IDF scoring, highlight, and faceted results
- Pluggable analyzers for 30+ languages with stemming, stop-words, and tokenization
- Rich query DSL: boolean, phrase, fuzzy, range, prefix, match, and geo distance
- Zero external dependencies -- pure Go, embedded in-process
- BoltDB-backed persistent storage with memory-mapped B+Tree indexes

## Best Use Cases

1. **CLI & Desktop Search** -- Add full-text search to Go command-line tools and desktop applications.
2. **Microservice Search** -- Embed search capability without standing up Elasticsearch or Solr.
3. **Document Catalogs** -- Index local documents with faceted navigation and relevance ranking.
4. **Geo-Spatial Search** -- Build location-aware Go applications with distance-based queries.
5. **Search-Driven UIs** -- Power typeahead, autocomplete, and highlighted search results in Go web apps.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Go | [`recipe_search_index`](go/cmd/recipe_search_index/main.go) | Create index, add recipe documents with custom field mappings, and batch-index multiple entries |
| Go | [`recipe_search_query`](go/cmd/recipe_search_query/main.go) | QueryString, Match, Term, and faceted search over indexed recipes |

## Limitations & Caveats

- Bleve stores only indexed terms and document identifiers, not the original documents (unless `Store` is set per field). Store original data separately or use the stored field option.
- Indexing is synchronous by default; use the `Batch` method for high-throughput insert workloads.
- The default storage engine (BoltDB) uses a single-writer model -- concurrent writes are serialized through a file lock.
- Bleve is not a database. It is a search indexing library designed to answer "which documents match this query?" rather than "show me document X".
- Index size grows with the number of unique terms. Large text fields with many unique tokens can produce substantial index files.

## Further Reading

- [Source Repository](https://github.com/blevesearch/bleve)
- [Bleve Documentation](https://blevesearch.com/docs/)
- [Go Package Documentation](https://pkg.go.dev/github.com/blevesearch/bleve/v2)
- [Bleve API Examples](https://github.com/blevesearch/bleve_examples)
