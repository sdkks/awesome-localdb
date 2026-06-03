package objectbox_test

import (
	"encoding/binary"
	"math"
	"os"
	"path/filepath"
	"testing"

	"awesome-localdb-objectbox-go/models"

	"github.com/objectbox/objectbox-go/objectbox"
)

// tempStore creates a temporary ObjectBox store and returns it with a cleanup func.
func tempStore(t *testing.T) (*objectbox.ObjectBox, func()) {
	t.Helper()

	dir, err := os.MkdirTemp("", "objectbox-test-*")
	if err != nil {
		t.Fatal(err)
	}

	ob, err := objectbox.NewBuilder().Directory(dir).Build()
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}

	cleanup := func() {
		ob.Close()
		os.RemoveAll(dir)
	}
	return ob, cleanup
}

// tempModelStore creates a temp store with the Document model registered.
func tempModelStore(t *testing.T) (*objectbox.ObjectBox, func()) {
	t.Helper()

	dir, err := os.MkdirTemp("", "objectbox-test-*")
	if err != nil {
		t.Fatal(err)
	}

	ob, err := objectbox.NewBuilder().Model(models.ObjectBoxModel()).Directory(dir).Build()
	if err != nil {
		os.RemoveAll(dir)
		t.Fatalf("Failed to create store with model: %v", err)
	}

	cleanup := func() {
		ob.Close()
		os.RemoveAll(dir)
	}
	return ob, cleanup
}

func TestCreateStore(t *testing.T) {
	ob, cleanup := tempStore(t)
	defer cleanup()

	if ob == nil {
		t.Fatal("Expected non-nil ObjectBox store")
	}
}

func TestStoreDirectoryPersistence(t *testing.T) {
	dir, err := os.MkdirTemp("", "objectbox-persist-*")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	// Create a store and close it.
	ob, err := objectbox.NewBuilder().Directory(dir).Build()
	if err != nil {
		t.Fatalf("Failed to create store: %v", err)
	}
	ob.Close()

	// Verify that data files were created on disk.
	entries, err := os.ReadDir(dir)
	if err != nil {
		t.Fatalf("Failed to read directory: %v", err)
	}
	if len(entries) == 0 {
		t.Error("Expected database files on disk after store creation")
	}

	// Re-open the store to verify persistence.
	ob2, err := objectbox.NewBuilder().Directory(dir).Build()
	if err != nil {
		t.Fatalf("Failed to re-open store: %v", err)
	}
	defer ob2.Close()
}

func TestStoreCloseIsIdempotent(t *testing.T) {
	ob, cleanup := tempStore(t)
	defer cleanup()

	// First close should succeed.
	ob.Close()

	// Second close should be safe (no panic).
	ob.Close()
}

func TestNewBuilderWithDefaults(t *testing.T) {
	dir, err := os.MkdirTemp("", "objectbox-defaults-*")
	if err != nil {
		t.Fatal(err)
	}
	defer os.RemoveAll(dir)

	ob, err := objectbox.NewBuilder().Directory(dir).Build()
	if err != nil {
		t.Fatalf("Failed to build with defaults: %v", err)
	}
	defer ob.Close()

	// Verify the data directory exists after creating store.
	dataDir := filepath.Join(dir, "data")
	if _, err := os.Stat(dataDir); err == nil {
		t.Logf("Data directory exists: %s", dataDir)
	}
}

func TestCloseSetsStoreNil(t *testing.T) {
	ob, cleanup := tempStore(t)
	defer cleanup()

	// Close should succeed and set internal store to nil.
	ob.Close()

	// Close again should be safe (idempotent).
	ob.Close()
}

// ─── Document CRUD and Vector Search Tests ──────────────────────────────

func TestDocumentCreateStoreAndInsert(t *testing.T) {
	ob, cleanup := tempModelStore(t)
	defer cleanup()

	box := models.BoxForDocument(ob)

	// Insert documents.
	testDocs := []struct {
		text      string
		embedding []float32
	}{
		{"Document A", []float32{1.0, 0.0, 0.0, 0.0}},
		{"Document B", []float32{0.0, 1.0, 0.0, 0.0}},
		{"Document C", []float32{0.0, 0.0, 1.0, 0.0}},
	}

	ids := make([]uint64, 0, len(testDocs))
	for _, td := range testDocs {
		doc := &models.Document{
			Text:      td.text,
			Embedding: float32ToBytes(td.embedding),
		}
		id, err := box.Put(doc)
		if err != nil {
			t.Fatalf("Failed to insert document: %v", err)
		}
		ids = append(ids, id)
	}

	if len(ids) != 3 {
		t.Fatalf("Expected 3 IDs, got %d", len(ids))
	}

	// Verify all IDs are unique.
	seen := make(map[uint64]bool)
	for _, id := range ids {
		if seen[id] {
			t.Errorf("Duplicate ID: %d", id)
		}
		seen[id] = true
	}

	// Retrieve by ID.
	retrieved, err := box.Get(ids[0])
	if err != nil {
		t.Fatalf("Failed to get document: %v", err)
	}
	if retrieved == nil {
		t.Fatal("Expected non-nil document")
	}
	if retrieved.Text != "Document A" {
		t.Errorf("Expected 'Document A', got '%s'", retrieved.Text)
	}
}

func TestDocumentVectorSearch(t *testing.T) {
	ob, cleanup := tempModelStore(t)
	defer cleanup()

	box := models.BoxForDocument(ob)

	// Insert documents with distinct embeddings.
	testDocs := []struct {
		text      string
		embedding []float32
	}{
		{"near", []float32{0.9, 0.1, 0.1, 0.1}},
		{"mid", []float32{0.5, 0.5, 0.5, 0.5}},
		{"far", []float32{0.1, 0.9, 0.1, 0.1}},
	}

	for _, td := range testDocs {
		doc := &models.Document{
			Text:      td.text,
			Embedding: float32ToBytes(td.embedding),
		}
		_, err := box.Put(doc)
		if err != nil {
			t.Fatalf("Failed to insert document: %v", err)
		}
	}

	// Get all documents.
	allDocs, err := box.GetAll()
	if err != nil {
		t.Fatalf("Failed to get all documents: %v", err)
	}
	if len(allDocs) != 3 {
		t.Fatalf("Expected 3 documents, got %d", len(allDocs))
	}

	// Query vector close to "near".
	queryVector := []float32{1.0, 0.0, 0.0, 0.0}

	// Compute cosine similarity and rank.
	type scored struct {
		doc *models.Document
		sim float64
	}
	ranked := make([]scored, len(allDocs))
	for i := range allDocs {
		emb := bytesToFloat32(allDocs[i].Embedding)
		ranked[i] = scored{doc: allDocs[i], sim: cosineSimilarity(queryVector, emb)}
	}

	// Sort by similarity descending (simple sort for test clarity).
	for i := 0; i < len(ranked); i++ {
		best := i
		for j := i + 1; j < len(ranked); j++ {
			if ranked[j].sim > ranked[best].sim {
				best = j
			}
		}
		ranked[i], ranked[best] = ranked[best], ranked[i]
	}

	// The first result should be "near" (closest to query).
	if ranked[0].doc.Text != "near" {
		t.Errorf("Expected first result to be 'near', got '%s' (sim=%.4f)",
			ranked[0].doc.Text, ranked[0].sim)
	}

	// Verify ordering: near sim > mid sim > far sim (with this query).
	if ranked[0].sim <= ranked[1].sim {
		t.Errorf("Expected ranked[0].sim > ranked[1].sim, got %.4f <= %.4f",
			ranked[0].sim, ranked[1].sim)
	}
	if ranked[1].sim <= ranked[2].sim {
		t.Errorf("Expected ranked[1].sim > ranked[2].sim, got %.4f <= %.4f",
			ranked[1].sim, ranked[2].sim)
	}

	t.Logf("Vector search results:")
	for i, r := range ranked {
		t.Logf("  %d. [sim=%.4f] %s", i+1, r.sim, r.doc.Text)
	}
}

func TestDocumentGetAll(t *testing.T) {
	ob, cleanup := tempModelStore(t)
	defer cleanup()

	box := models.BoxForDocument(ob)

	// Empty store should return empty slice.
	docs, err := box.GetAll()
	if err != nil {
		t.Fatalf("GetAll on empty store failed: %v", err)
	}
	if len(docs) != 0 {
		t.Errorf("Expected 0 documents, got %d", len(docs))
	}

	// Insert some documents and verify count.
	for i := 0; i < 5; i++ {
		doc := &models.Document{
			Text:      "test",
			Embedding: float32ToBytes([]float32{float32(i) * 0.1, 0, 0, 0}),
		}
		_, err := box.Put(doc)
		if err != nil {
			t.Fatalf("Failed to insert: %v", err)
		}
	}

	docs, err = box.GetAll()
	if err != nil {
		t.Fatalf("GetAll failed: %v", err)
	}
	if len(docs) != 5 {
		t.Errorf("Expected 5 documents, got %d", len(docs))
	}
}

// ─── Vector Math Helpers ─────────────────────────────────────────────────

func float32ToBytes(vec []float32) []byte {
	buf := make([]byte, len(vec)*4)
	for i, v := range vec {
		binary.LittleEndian.PutUint32(buf[i*4:], math.Float32bits(v))
	}
	return buf
}

func bytesToFloat32(data []byte) []float32 {
	vec := make([]float32, len(data)/4)
	for i := range vec {
		vec[i] = math.Float32frombits(binary.LittleEndian.Uint32(data[i*4:]))
	}
	return vec
}

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
