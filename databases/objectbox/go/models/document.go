// Package models provides test entities for ObjectBox Go recipes.
// The Document entity demonstrates vector storage with byte-serialized float32 embeddings.
package models

//go:generate go run github.com/objectbox/objectbox-go/cmd/objectbox-gogen

// Document represents a text document with an embedding vector.
// The Embedding field stores float32 values serialized as little-endian bytes.
type Document struct {
	Id        uint64
	Text      string
	Embedding []byte
}
