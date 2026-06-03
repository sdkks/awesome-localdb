// Package main demonstrates Bleve full-text indexing: creating an index,
// defining custom field mappings for recipe documents, indexing multiple recipes
// via batch, and performing a basic search to verify the index.
package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"

	"github.com/blevesearch/bleve/v2"
	"github.com/blevesearch/bleve/v2/mapping"
)

// Recipe represents a document to be indexed.
type Recipe struct {
	Name        string   `json:"name"`
	Cuisine     string   `json:"cuisine"`
	Ingredients []string `json:"ingredients"`
}

func main() {
	// Create a temporary directory for the index.
	tmpDir, err := os.MkdirTemp("", "bleve-recipe-index-*")
	if err != nil {
		log.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	indexPath := filepath.Join(tmpDir, "recipes.bleve")
	fmt.Println("Index path:", indexPath)

	// Build a custom index mapping for recipe documents.
	indexMapping := bleve.NewIndexMapping()

	// Configure the name field for full-text search with highlighting.
	nameFieldMapping := bleve.NewTextFieldMapping()
	nameFieldMapping.Analyzer = "en"
	nameFieldMapping.Store = true
	nameFieldMapping.IncludeTermVectors = true
	indexMapping.DefaultMapping.AddFieldMappingsAt("name", nameFieldMapping)

	// Cuisine is a keyword field (exact match).
	cuisineFieldMapping := bleve.NewTextFieldMapping()
	cuisineFieldMapping.Analyzer = "keyword"
	cuisineFieldMapping.Store = true
	indexMapping.DefaultMapping.AddFieldMappingsAt("cuisine", cuisineFieldMapping)

	// Ingredients use the standard analyzer.
	ingredientsFieldMapping := bleve.NewTextFieldMapping()
	ingredientsFieldMapping.Analyzer = "en"
	indexMapping.DefaultMapping.AddFieldMappingsAt("ingredients", ingredientsFieldMapping)

	// Create or open the index.
	index, err := bleve.New(indexPath, indexMapping)
	if err != nil {
		log.Fatal(err)
	}
	defer index.Close()

	// Recipes to index.
	recipes := []Recipe{
		{
			Name:        "Classic Margherita Pizza",
			Cuisine:     "Italian",
			Ingredients: []string{"pizza dough", "tomato sauce", "fresh mozzarella", "basil", "olive oil"},
		},
		{
			Name:        "Chicken Tikka Masala",
			Cuisine:     "Indian",
			Ingredients: []string{"chicken", "yogurt", "tomato puree", "garam masala", "cream", "garlic"},
		},
		{
			Name:        "Spaghetti Carbonara",
			Cuisine:     "Italian",
			Ingredients: []string{"spaghetti", "guanciale", "egg yolks", "pecorino romano", "black pepper"},
		},
	}

	// Batch index all recipes.
	batch := index.NewBatch()
	for i, r := range recipes {
		id := fmt.Sprintf("recipe-%d", i+1)
		if err := batch.Index(id, r); err != nil {
			log.Fatalf("batch index %s: %v", id, err)
		}
		fmt.Printf("Indexed: %s (%s)\n", r.Name, r.Cuisine)
	}
	if err := index.Batch(batch); err != nil {
		log.Fatal(err)
	}

	// Verify with a simple search.
	query := bleve.NewQueryStringQuery("mozzarella")
	searchRequest := bleve.NewSearchRequest(query)
	searchResult, err := index.Search(searchRequest)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Printf("\nSearch for 'mozzarella': %d result(s)\n", searchResult.Total)
	for _, hit := range searchResult.Hits {
		fmt.Printf("  - %s (score: %.4f)\n", hit.ID, hit.Score)
	}

	fmt.Println("\nDone.")
}

// Ensure unused import is not flagged (mapping is used indirectly through
// AddFieldMappingsAt, but the import is needed for the custom setup).
var _ = mapping.NewIndexMapping
