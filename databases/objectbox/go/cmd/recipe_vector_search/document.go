// Package main demonstrates the ObjectBox Go API: creating a store,
// persisting objects with vector properties, and performing vector
// similarity search (brute-force cosine similarity in Go code).
//
// Note: ObjectBox Go v1.9.0 does not expose native HNSW nearest-neighbor
// search. This recipe stores float32 embeddings as byte vectors and computes
// cosine similarity in Go after retrieval. For native ANN search, use
// ObjectBox Python (v4+), Java/Kotlin, Swift, or Dart/Flutter bindings.
package main

//go:generate go run github.com/objectbox/objectbox-go/cmd/objectbox-gogen

// Document represents a text document with an embedding vector.
// The Embedding field stores float32 values serialized as little-endian bytes.
type Document struct {
	Id        uint64
	Text      string
	Embedding []byte
}
