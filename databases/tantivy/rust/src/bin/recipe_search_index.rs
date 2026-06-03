//! Recipe: Search Index
//! Database: Tantivy
//! Description: Demonstrates creating a full-text search index with structured fields
//!              (title, cuisine, ingredients, instructions, difficulty) and BM25 scoring.
//!
//! Usage: cargo run --bin recipe_search_index

use std::fs;
use std::path::Path;
use tantivy::collector::TopDocs;
use tantivy::query::QueryParser;
use tantivy::schema::*;
use tantivy::{doc, Index, IndexWriter, ReloadPolicy, TantivyDocument};

fn main() -> tantivy::Result<()> {
    let index_path = Path::new("recipe_index");

    // ── 1. Define schema ────────────────────────────────────────────────
    let mut schema_builder = Schema::builder();
    let title = schema_builder.add_text_field("title", TEXT | STORED);
    let cuisine = schema_builder.add_text_field("cuisine", STRING | STORED);
    let ingredients = schema_builder.add_text_field("ingredients", TEXT);
    let instructions = schema_builder.add_text_field("instructions", TEXT);
    let difficulty = schema_builder.add_text_field("difficulty", STRING | STORED);
    let schema = schema_builder.build();

    // ── 2. Ensure the index directory exists ────────────────────────────
    if index_path.exists() {
        fs::remove_dir_all(index_path).expect("Failed to remove previous index");
    }
    fs::create_dir_all(index_path).expect("Failed to create index directory");

    // ── 3. Create index ─────────────────────────────────────────────────
    let index = Index::create_in_dir(index_path, schema.clone())?;
    let mut writer: IndexWriter = index.writer(50_000_000)?;

    println!("Index created at {:?}", index_path);

    // ── 4. Index recipe documents ───────────────────────────────────────
    let recipes = vec![
        (
            "Spaghetti Carbonara",
            "Italian",
            "spaghetti, eggs, guanciale, pecorino romano, black pepper",
            "Cook spaghetti al dente. Fry guanciale until crispy. Mix eggs with pecorino and pepper. Toss hot pasta with guanciale, then fold in egg mixture off heat.",
            "Medium",
        ),
        (
            "Chicken Tikka Masala",
            "Indian",
            "chicken breast, yogurt, tomato puree, cream, garam masala, turmeric, cumin, ginger, garlic",
            "Marinate chicken in yogurt and spices for 2 hours. Grill until charred. Simmer tomato puree with cream and spices. Add chicken and cook through.",
            "Medium",
        ),
        (
            "Caesar Salad",
            "American",
            "romaine lettuce, croutons, parmesan cheese, lemon juice, olive oil, anchovy paste, garlic",
            "Whisk lemon juice, olive oil, anchovy paste, and garlic for dressing. Toss romaine with dressing. Top with croutons and shaved parmesan.",
            "Easy",
        ),
        (
            "Tonkotsu Ramen",
            "Japanese",
            "pork bones, ramen noodles, soy sauce, miso paste, green onions, soft-boiled egg, chashu pork, nori",
            "Boil pork bones for 12 hours for the broth. Cook ramen noodles separately. Assemble bowl with broth, noodles, sliced chashu, halved egg, nori, and green onions.",
            "Hard",
        ),
        (
            "Fish Tacos",
            "Mexican",
            "white fish fillets, corn tortillas, cabbage, lime, sour cream, cilantro, chili powder, cumin",
            "Season fish with chili powder and cumin, pan-fry until flaky. Warm tortillas. Assemble with fish, shredded cabbage, sour cream, cilantro, and a squeeze of lime.",
            "Easy",
        ),
    ];

    for (title_text, cuisine_text, ingredients_text, instructions_text, difficulty_text) in &recipes
    {
        writer.add_document(doc!(
            title => *title_text,
            cuisine => *cuisine_text,
            ingredients => *ingredients_text,
            instructions => *instructions_text,
            difficulty => *difficulty_text,
        ))?;
    }

    // ── 5. Commit to make documents searchable ──────────────────────────
    writer.commit()?;
    println!("Indexed {} recipes.", recipes.len());

    // ── 6. Verify: Run a quick search ───────────────────────────────────
    let reader = index
        .reader_builder()
        .reload_policy(ReloadPolicy::Manual)
        .try_into()?;
    reader.reload()?;
    let searcher = reader.searcher();
    let query_parser = QueryParser::for_index(&index, vec![title, ingredients, instructions]);
    let query = query_parser.parse_query("chicken")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(5))?;

    println!("\nQuick verification search for 'chicken':");
    for (_score, doc_address) in top_docs {
        let doc = searcher.doc::<TantivyDocument>(doc_address)?;
        if let Some(name) = doc.get_first(title).and_then(|v| v.as_str()) {
            println!("  Found: {}", name);
        }
    }

    println!("\nIndexing complete.");

    // Writer is dropped here, releasing the write lock
    Ok(())
}
