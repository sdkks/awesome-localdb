package bleve_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/blevesearch/bleve/v2"
)

// tempIndex creates a temporary Bleve index and returns it plus a cleanup func.
func tempIndex(t *testing.T) (bleve.Index, func()) {
	t.Helper()
	dir, err := os.MkdirTemp("", "bleve-test-*")
	if err != nil {
		t.Fatal(err)
	}

	indexPath := filepath.Join(dir, "test.bleve")
	index, err := bleve.New(indexPath, bleve.NewIndexMapping())
	if err != nil {
		t.Fatal(err)
	}

	cleanup := func() {
		index.Close()
		os.RemoveAll(dir)
	}
	return index, cleanup
}

func TestCreateIndex(t *testing.T) {
	idx, cleanup := tempIndex(t)
	defer cleanup()

	// Verify the index is usable by checking its name ends with "test.bleve".
	name := idx.Name()
	if filepath.Base(name) != "test.bleve" {
		t.Errorf("expected index name ending with 'test.bleve', got %q", name)
	}
}

func TestIndexDocument(t *testing.T) {
	idx, cleanup := tempIndex(t)
	defer cleanup()

	doc := map[string]interface{}{
		"name":    "Test Recipe",
		"cuisine": "Test",
	}
	err := idx.Index("recipe-1", doc)
	if err != nil {
		t.Fatalf("Index: %v", err)
	}

	// Count documents.
	count, err := idx.DocCount()
	if err != nil {
		t.Fatalf("DocCount: %v", err)
	}
	if count != 1 {
		t.Errorf("expected 1 document, got %d", count)
	}
}

func TestSearchTermQuery(t *testing.T) {
	idx, cleanup := tempIndex(t)
	defer cleanup()

	// Index sample documents.
	recipes := []map[string]interface{}{
		{"name": "Pizza Margherita", "cuisine": "Italian"},
		{"name": "Pad Thai", "cuisine": "Thai"},
		{"name": "Spaghetti Carbonara", "cuisine": "Italian"},
	}
	for i, r := range recipes {
		id := string(rune('a'+i)) + "-recipe"
		if err := idx.Index(id, r); err != nil {
			t.Fatalf("Index %s: %v", id, err)
		}
	}

	// Search for Italian cuisine (analyzer lowercases to "italian").
	termQuery := bleve.NewTermQuery("italian")
	termQuery.SetField("cuisine")
	req := bleve.NewSearchRequest(termQuery)
	result, err := idx.Search(req)
	if err != nil {
		t.Fatalf("Search: %v", err)
	}

	if result.Total != 2 {
		t.Errorf("expected 2 Italian recipes, got %d", result.Total)
	}
}

func TestSearchQueryString(t *testing.T) {
	idx, cleanup := tempIndex(t)
	defer cleanup()

	recipes := []map[string]interface{}{
		{"name": "Pizza Margherita", "ingredients": "tomato mozzarella basil"},
		{"name": "Chicken Curry", "ingredients": "chicken coconut curry"},
		{"name": "Tomato Soup", "ingredients": "tomato basil cream"},
	}
	for i, r := range recipes {
		id := string(rune('a'+i)) + "-recipe"
		if err := idx.Index(id, r); err != nil {
			t.Fatalf("Index %s: %v", id, err)
		}
	}

	// Query string search for "chicken".
	query := bleve.NewQueryStringQuery("chicken")
	req := bleve.NewSearchRequest(query)
	result, err := idx.Search(req)
	if err != nil {
		t.Fatalf("Search: %v", err)
	}

	if result.Total != 1 {
		t.Errorf("expected 1 result for 'chicken', got %d", result.Total)
	}

	// "tomato" should match two recipes.
	query2 := bleve.NewQueryStringQuery("tomato")
	req2 := bleve.NewSearchRequest(query2)
	result2, err := idx.Search(req2)
	if err != nil {
		t.Fatalf("Search: %v", err)
	}
	if result2.Total != 2 {
		t.Errorf("expected 2 results for 'tomato', got %d", result2.Total)
	}
}

func TestDeleteDocument(t *testing.T) {
	idx, cleanup := tempIndex(t)
	defer cleanup()

	doc := map[string]interface{}{"name": "To Be Deleted"}
	err := idx.Index("del-1", doc)
	if err != nil {
		t.Fatalf("Index: %v", err)
	}

	err = idx.Delete("del-1")
	if err != nil {
		t.Fatalf("Delete: %v", err)
	}

	count, err := idx.DocCount()
	if err != nil {
		t.Fatalf("DocCount: %v", err)
	}
	if count != 0 {
		t.Errorf("expected 0 documents after delete, got %d", count)
	}
}

func TestBatchIndex(t *testing.T) {
	idx, cleanup := tempIndex(t)
	defer cleanup()

	batch := idx.NewBatch()
	for i := 0; i < 10; i++ {
		id := string(rune('a'+i)) + "-recipe"
		doc := map[string]interface{}{
			"name":    "Batch Recipe",
			"cuisine": "Test",
		}
		if err := batch.Index(id, doc); err != nil {
			t.Fatalf("batch.Index: %v", err)
		}
	}
	err := idx.Batch(batch)
	if err != nil {
		t.Fatalf("Batch: %v", err)
	}

	count, err := idx.DocCount()
	if err != nil {
		t.Fatalf("DocCount: %v", err)
	}
	if count != 10 {
		t.Errorf("expected 10 documents, got %d", count)
	}
}
