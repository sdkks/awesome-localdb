// Package main demonstrates Bleve search queries: query string, match phrase,
// term, boolean, and faceted search over an existing recipe index. If the
// index does not exist, it creates one with sample recipe data.
package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"

	"github.com/blevesearch/bleve/v2"
	"github.com/blevesearch/bleve/v2/search/query"
)

func main() {
	// Create a temporary directory for the index.
	tmpDir, err := os.MkdirTemp("", "bleve-recipe-query-*")
	if err != nil {
		log.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	indexPath := filepath.Join(tmpDir, "recipes.bleve")
	fmt.Println("Index path:", indexPath)

	// Create index and populate with sample data.
	index, err := bleve.New(indexPath, bleve.NewIndexMapping())
	if err != nil {
		log.Fatal(err)
	}
	defer index.Close()

	// Index sample recipes.
	recipes := []map[string]interface{}{
		{"name": "Classic Margherita Pizza", "cuisine": "Italian", "ingredients": "tomato mozzarella basil"},
		{"name": "Chicken Tikka Masala", "cuisine": "Indian", "ingredients": "chicken yogurt garam masala cream"},
		{"name": "Spaghetti Carbonara", "cuisine": "Italian", "ingredients": "spaghetti guanciale egg pecorino pepper"},
		{"name": "Pad Thai", "cuisine": "Thai", "ingredients": "rice noodles shrimp tamarind peanuts bean sprouts"},
		{"name": "Beef Tacos", "cuisine": "Mexican", "ingredients": "beef tortillas cilantro lime salsa"},
	}
	for i, r := range recipes {
		id := fmt.Sprintf("recipe-%d", i+1)
		if err := index.Index(id, r); err != nil {
			log.Fatalf("index %s: %v", id, err)
		}
		fmt.Printf("Indexed: %s (%s)\n", r["name"], r["cuisine"])
	}

	// Query 1: Query String
	fmt.Println("\n--- Query String: 'chicken' ---")
	q := bleve.NewQueryStringQuery("chicken")
	runSearch(index, q)

	// Query 2: Match Phrase
	fmt.Println("\n--- Match Phrase: 'Classic Margherita' ---")
	mq := bleve.NewMatchPhraseQuery("Classic Margherita")
	mq.SetField("name")
	runSearch(index, mq)

	// Query 3: Term Query (exact match on cuisine — analyzer lowercases).
	fmt.Println("\n--- Term Query: cuisine:'italian' ---")
	tq := bleve.NewTermQuery("italian")
	tq.SetField("cuisine")
	runSearch(index, tq)

	// Query 4: Boolean Query (Italian AND pepper)
	fmt.Println("\n--- Boolean: cuisine:'italian' AND ingredients:'pepper' ---")
	bq := bleve.NewBooleanQuery()
	bq.AddMust(bleve.NewTermQuery("italian"))
	bq.AddMust(bleve.NewTermQuery("pepper"))
	runSearch(index, bq)

	// Query 5: Faceted search over cuisines.
	fmt.Println("\n--- Faceted Search: '*' grouped by cuisine ---")
	facet := bleve.NewFacetRequest("cuisine", 10)
	fsr := bleve.NewSearchRequest(bleve.NewMatchAllQuery())
	fsr.AddFacet("cuisine-facet", facet)
	fsr.Size = 0 // Only facets, no hits.
	fsResult, err := index.Search(fsr)
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("Total documents: %d\n", fsResult.Total)
	fr := fsResult.Facets["cuisine-facet"]
	if fr != nil {
		for _, term := range fr.Terms.Terms() {
			fmt.Printf("  %s: %d\n", term.Term, term.Count)
		}
	}

	fmt.Println("\nDone.")
}

func runSearch(index bleve.Index, q query.Query) {
	searchRequest := bleve.NewSearchRequest(q)
	searchRequest.Size = 5
	searchResult, err := index.Search(searchRequest)
	if err != nil {
		log.Fatalf("search: %v", err)
	}
	fmt.Printf("Results: %d\n", searchResult.Total)
	for _, hit := range searchResult.Hits {
		fmt.Printf("  - %s (score: %.4f)\n", hit.ID, hit.Score)
		if hit.Fields != nil {
			fmt.Printf("    fields: %v\n", hit.Fields)
		}
	}
}
