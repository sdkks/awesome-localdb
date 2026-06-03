//! Recipe: Search Query
//! Database: Tantivy
//! Description: Demonstrates searching a Tantivy index with BM25-ranked queries,
//!              including simple term queries, phrase queries, and field-specific searches.
//!
//! Usage: cargo run --bin recipe_search_query

use std::path::Path;
use tantivy::collector::TopDocs;
use tantivy::query::{PhraseQuery, QueryParser};
use tantivy::schema::*;
use tantivy::{Index, ReloadPolicy, TantivyDocument};

fn main() -> tantivy::Result<()> {
    let index_path = Path::new("recipe_index");

    // ── 1. Open existing index ──────────────────────────────────────────
    let index = Index::open_in_dir(index_path)?;
    let schema = index.schema();

    // Resolve fields
    let title = schema.get_field("title").expect("title field not found");
    let cuisine = schema
        .get_field("cuisine")
        .expect("cuisine field not found");
    let ingredients = schema
        .get_field("ingredients")
        .expect("ingredients field not found");
    let instructions = schema
        .get_field("instructions")
        .expect("instructions field not found");
    let difficulty = schema
        .get_field("difficulty")
        .expect("difficulty field not found");

    let reader = index
        .reader_builder()
        .reload_policy(ReloadPolicy::Manual)
        .try_into()?;
    reader.reload()?;
    let searcher = reader.searcher();

    let query_parser =
        QueryParser::for_index(&index, vec![title, ingredients, instructions, cuisine]);

    fn print_results(
        searcher: &tantivy::Searcher,
        _schema: &Schema,
        title: Field,
        cuisine: Field,
        difficulty: Field,
        top_docs: &[(tantivy::Score, tantivy::DocAddress)],
    ) {
        if top_docs.is_empty() {
            println!("  (no results)");
            return;
        }
        for (score, doc_address) in top_docs {
            if let Ok(doc) = searcher.doc::<TantivyDocument>(*doc_address) {
                let name = doc
                    .get_first(title)
                    .and_then(|v| v.as_str())
                    .unwrap_or("(unknown)");
                let cuis = doc
                    .get_first(cuisine)
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                let diff = doc
                    .get_first(difficulty)
                    .and_then(|v| v.as_str())
                    .unwrap_or("");
                println!("  [{:.4}] {} | {} | {}", score, name, cuis, diff);
            }
        }
    }

    // ── 2. Simple term search ───────────────────────────────────────────
    println!("=== Search 1: 'chicken' ===");
    let query = query_parser.parse_query("chicken")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(5))?;
    print_results(&searcher, &schema, title, cuisine, difficulty, &top_docs);

    // ── 3. Multi-term search (BM25 combines scores) ─────────────────────
    println!("\n=== Search 2: 'pork noodles' ===");
    let query = query_parser.parse_query("pork noodles")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(5))?;
    print_results(&searcher, &schema, title, cuisine, difficulty, &top_docs);

    // ── 4. Phrase search ────────────────────────────────────────────────
    println!("\n=== Search 3: phrase 'black pepper' ===");
    let phrase_query = PhraseQuery::new_with_offset(vec![
        (0, tantivy::Term::from_field_text(ingredients, "black")),
        (1, tantivy::Term::from_field_text(ingredients, "pepper")),
    ]);
    let top_docs = searcher.search(&phrase_query, &TopDocs::with_limit(5))?;
    print_results(&searcher, &schema, title, cuisine, difficulty, &top_docs);

    // ── 5. Filtered search: Italian cuisine ─────────────────────────────
    println!("\n=== Search 4: Italian + 'cheese' ===");
    let query = query_parser.parse_query("cheese")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(5))?;
    // Filter to Italian cuisine only
    let italian_results: Vec<_> = top_docs
        .into_iter()
        .filter(|(_score, doc_address)| {
            searcher
                .doc::<TantivyDocument>(*doc_address)
                .ok()
                .and_then(|doc| {
                    doc.get_first(cuisine)
                        .and_then(|v| v.as_str())
                        .map(|c| c == "Italian")
                })
                .unwrap_or(false)
        })
        .collect();
    print_results(
        &searcher,
        &schema,
        title,
        cuisine,
        difficulty,
        &italian_results,
    );

    // ── 6. All Easy recipes (term query on STRING field) ─────────────────
    println!("\n=== Search 5: difficulty:Easy ===");
    let easy_term = tantivy::Term::from_field_text(difficulty, "Easy");
    let easy_query =
        tantivy::query::TermQuery::new(easy_term, tantivy::schema::IndexRecordOption::Basic);
    let top_docs = searcher.search(&easy_query, &TopDocs::with_limit(5))?;
    print_results(&searcher, &schema, title, cuisine, difficulty, &top_docs);

    println!("\nSearch demo complete.");
    Ok(())
}
