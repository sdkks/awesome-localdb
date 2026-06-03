// Package main demonstrates the ObjectBox Go API: creating a store,
// persisting objects with vector properties, and performing vector
// similarity search (brute-force cosine similarity in Go code).
//
// Note: ObjectBox Go v1.9.0 does not expose native HNSW nearest-neighbor
// search. This recipe stores float32 embeddings as byte vectors and computes
// cosine similarity in Go after retrieval. For native ANN vector search,
// use ObjectBox Python (v4+), Java/Kotlin, Swift, or Dart/Flutter bindings.
//
// Prerequisites: ObjectBox native library must be installed via the
// install script before running this recipe:
//
//	bash <(curl -s https://raw.githubusercontent.com/objectbox/objectbox-go/main/install.sh)
package main

import (
	"encoding/binary"
	"fmt"
	"log"
	"math"
	"os"
	"path/filepath"

	"github.com/objectbox/objectbox-go/objectbox"
)

func main() {
	// Create a temporary directory for the database file.
	tmpDir, err := os.MkdirTemp("", "objectbox-vector-*")
	if err != nil {
		log.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	dbPath := filepath.Join(tmpDir, "vectors")
	fmt.Println("Database:", dbPath)

	// Open (or create) the ObjectBox store with the generated model.
	ob, err := objectbox.NewBuilder().Model(ObjectBoxModel()).Directory(dbPath).Build()
	if err != nil {
		log.Fatalf("Failed to create store: %v", err)
	}
	defer ob.Close()

	box := BoxForDocument(ob)

	// Insert sample documents with 4-dimensional embeddings.
	docs := []struct {
		text      string
		embedding []float32
	}{
		{"ObjectBox is an on-device vector database", []float32{0.1, 0.2, 0.3, 0.4}},
		{"Vector search enables semantic similarity", []float32{0.9, 0.8, 0.7, 0.6}},
		{"Embedded databases run without a server", []float32{0.15, 0.25, 0.35, 0.45}},
		{"Go is great for systems programming", []float32{0.85, 0.75, 0.65, 0.55}},
		{"IoT devices need efficient local storage", []float32{0.12, 0.22, 0.32, 0.42}},
	}

	insertedIDs := make([]uint64, len(docs))
	for i, d := range docs {
		doc := &Document{
			Text:      d.text,
			Embedding: float32ToBytes(d.embedding),
		}
		id, err := box.Put(doc)
		if err != nil {
			log.Fatalf("Failed to insert document: %v", err)
		}
		insertedIDs[i] = id
	}
	fmt.Printf("Inserted %d documents\n", len(insertedIDs))

	// Retrieve a specific document by ID.
	doc, err := box.Get(insertedIDs[0])
	if err != nil {
		log.Fatalf("Failed to get document: %v", err)
	}
	fmt.Printf("\nRetrieved doc[0]: %s\n", doc.Text)

	// Retrieve all documents for vector search.
	allDocs, err := box.GetAll()
	if err != nil {
		log.Fatalf("Failed to get all documents: %v", err)
	}

	// Vector search: rank all documents by cosine similarity to the query.
	queryVector := []float32{0.1, 0.2, 0.3, 0.4}

	type scored struct {
		doc *Document
		sim float64
	}
	ranked := make([]scored, len(allDocs))
	for i := range allDocs {
		emb := bytesToFloat32(allDocs[i].Embedding)
		ranked[i] = scored{doc: allDocs[i], sim: cosineSimilarity(queryVector, emb)}
	}

	// Sort by similarity descending (selection sort for clarity).
	for i := 0; i < len(ranked); i++ {
		best := i
		for j := i + 1; j < len(ranked); j++ {
			if ranked[j].sim > ranked[best].sim {
				best = j
			}
		}
		ranked[i], ranked[best] = ranked[best], ranked[i]
	}

	fmt.Println("\nVector search results (cosine similarity):")
	for i, r := range ranked {
		emb := bytesToFloat32(r.doc.Embedding)
		fmt.Printf("  %d. [id=%d sim=%.4f emb=%v] %s\n",
			i+1, r.doc.Id, r.sim, emb, r.doc.Text)
	}

	fmt.Println("\nObjectBox store closed successfully")
}

// float32ToBytes serializes a float32 slice to a little-endian byte slice.
func float32ToBytes(vec []float32) []byte {
	buf := make([]byte, len(vec)*4)
	for i, v := range vec {
		binary.LittleEndian.PutUint32(buf[i*4:], math.Float32bits(v))
	}
	return buf
}

// bytesToFloat32 deserializes a little-endian byte slice to a float32 slice.
func bytesToFloat32(data []byte) []float32 {
	vec := make([]float32, len(data)/4)
	for i := range vec {
		vec[i] = math.Float32frombits(binary.LittleEndian.Uint32(data[i*4:]))
	}
	return vec
}

// cosineSimilarity computes the cosine similarity between two equal-length float32 vectors.
func cosineSimilarity(a, b []float32) float64 {
	if len(a) != len(b) || len(a) == 0 {
		return 0
	}
	var dot, normA, normB float64
	for i := range a {
		dot += float64(a[i]) * float64(b[i])
		normA += float64(a[i]) * float64(a[i])
		normB += float64(b[i]) * float64(b[i])
	}
	if normA == 0 || normB == 0 {
		return 0
	}
	return dot / (math.Sqrt(normA) * math.Sqrt(normB))
}
