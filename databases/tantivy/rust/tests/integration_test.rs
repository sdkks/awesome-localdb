/// Integration tests for the Tantivy Rust recipes.
/// These tests create a temporary index, index documents, and verify search results.
use tantivy::collector::TopDocs;
use tantivy::query::QueryParser;
use tantivy::schema::*;
use tantivy::{doc, Index, IndexWriter, ReloadPolicy, TantivyDocument};

fn setup_index() -> tantivy::Result<(Index, Field, Field, Field)> {
    let mut schema_builder = Schema::builder();
    let title = schema_builder.add_text_field("title", TEXT | STORED);
    let body = schema_builder.add_text_field("body", TEXT | STORED);
    let category = schema_builder.add_text_field("category", STRING | STORED);
    let schema = schema_builder.build();

    let index = Index::create_in_ram(schema);
    Ok((index, title, body, category))
}

#[test]
fn test_create_and_search_basic_index() -> tantivy::Result<()> {
    let (index, title, body, _category) = setup_index()?;

    // Index documents
    let mut writer: IndexWriter = index.writer(50_000_000)?;
    writer.add_document(doc!(
        title => "The Old Man and the Sea",
        body => "He was an old man who fished alone in a skiff in the Gulf Stream."
    ))?;
    writer.add_document(doc!(
        title => "Moby-Dick",
        body => "Call me Ishmael. Some years ago the great whale Moby Dick."
    ))?;
    writer.add_document(doc!(
        title => "Twenty Thousand Leagues Under the Sea",
        body => "The sea is everything. It covers seven tenths of the globe. A sea monster terrorizes ships."
    ))?;
    writer.commit()?;

    // Search
    let reader = index
        .reader_builder()
        .reload_policy(ReloadPolicy::Manual)
        .try_into()?;
    reader.reload()?;
    let searcher = reader.searcher();

    let query_parser = QueryParser::for_index(&index, vec![title, body]);

    // Search for "sea" — should match docs 1 and 3
    let query = query_parser.parse_query("sea")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;
    assert!(
        !top_docs.is_empty(),
        "Should find documents containing 'sea'"
    );

    let doc = searcher.doc::<TantivyDocument>(top_docs[0].1)?;
    assert!(doc.get_first(title).and_then(|v| v.as_str()).is_some());

    // Search for "whale" — should match doc 2 ("Moby-Dick")
    let query = query_parser.parse_query("whale")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;
    assert!(
        !top_docs.is_empty(),
        "Should find documents containing 'whale'"
    );
    let doc = searcher.doc::<TantivyDocument>(top_docs[0].1)?;
    let found_title = doc.get_first(title).and_then(|v| v.as_str()).unwrap_or("");
    assert!(
        found_title.contains("Moby"),
        "Expected Moby-Dick, got: {}",
        found_title
    );

    // Search for something not in index
    let query = query_parser.parse_query("zyxwvut_nonexistent")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;
    assert!(
        top_docs.is_empty(),
        "Should find no results for nonsense term"
    );

    Ok(())
}

#[test]
fn test_bm25_relevance_ranking() -> tantivy::Result<()> {
    let (index, title, body, _category) = setup_index()?;

    // Index documents with varying frequency of "sea"
    let mut writer: IndexWriter = index.writer(50_000_000)?;
    // Doc 1: "sea" appears once
    writer.add_document(doc!(
        title => "Sea Document Once",
        body => "The sea is blue."
    ))?;
    // Doc 2: "sea" appears three times
    writer.add_document(doc!(
        title => "Sea Document Thrice",
        body => "The sea is vast. The sea is deep. The sea is mysterious."
    ))?;
    // Doc 3: "sea" in title and body
    writer.add_document(doc!(
        title => "The Sea Wolf",
        body => "A story about the sea and a wolf."
    ))?;
    writer.commit()?;

    // Search
    let reader = index
        .reader_builder()
        .reload_policy(ReloadPolicy::Manual)
        .try_into()?;
    reader.reload()?;
    let searcher = reader.searcher();

    let query_parser = QueryParser::for_index(&index, vec![title, body]);
    let query = query_parser.parse_query("sea")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;

    // Should find 3 results
    assert_eq!(top_docs.len(), 3, "Should find all 3 documents");

    // Scores should be descending (first result has highest score)
    assert!(
        top_docs[0].0 >= top_docs[1].0,
        "Results should be sorted by descending score"
    );
    assert!(
        top_docs[1].0 >= top_docs[2].0,
        "Results should be sorted by descending score"
    );

    // Highest-scored doc should be "Sea Document Thrice" (most mentions of "sea")
    let top_doc = searcher.doc::<TantivyDocument>(top_docs[0].1)?;
    let top_title = top_doc
        .get_first(title)
        .and_then(|v| v.as_str())
        .unwrap_or("");
    assert_eq!(
        top_title, "Sea Document Thrice",
        "Document with most 'sea' mentions should rank highest, got: {}",
        top_title
    );

    Ok(())
}

#[test]
fn test_index_update_and_commit() -> tantivy::Result<()> {
    let (index, title, body, _category) = setup_index()?;

    // First batch
    {
        let mut writer: IndexWriter = index.writer(50_000_000)?;
        writer.add_document(doc!(
            title => "First Commit Doc",
            body => "This doc is in the first commit."
        ))?;
        writer.commit()?;
    } // Writer dropped here, releasing the lock

    // Verify first commit is searchable
    {
        let reader = index
            .reader_builder()
            .reload_policy(ReloadPolicy::Manual)
            .try_into()?;
        reader.reload()?;
        let searcher = reader.searcher();
        let query_parser = QueryParser::for_index(&index, vec![title, body]);
        let query = query_parser.parse_query("first")?;
        let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;
        assert_eq!(top_docs.len(), 1, "Should find document from first commit");
    }

    // Second batch — with a new writer
    let mut writer: IndexWriter = index.writer(50_000_000)?;
    writer.add_document(doc!(
        title => "Second Commit Doc",
        body => "This doc appears after the second commit."
    ))?;
    writer.commit()?;

    // Verify both commits are searchable
    {
        let reader = index
            .reader_builder()
            .reload_policy(ReloadPolicy::Manual)
            .try_into()?;
        reader.reload()?;
        let searcher = reader.searcher();
        let query_parser = QueryParser::for_index(&index, vec![title, body]);
        let query = query_parser.parse_query("commit")?;
        let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;
        assert_eq!(
            top_docs.len(),
            2,
            "Should find both documents after second commit"
        );
    }

    Ok(())
}

#[test]
fn test_in_memory_index() -> tantivy::Result<()> {
    // Create a purely in-memory index
    let mut schema_builder = Schema::builder();
    let text = schema_builder.add_text_field("text", TEXT | STORED);
    let schema = schema_builder.build();
    let index = Index::create_in_ram(schema);

    let mut writer: IndexWriter = index.writer(50_000_000)?;
    writer.add_document(doc!(text => "hello world"))?;
    writer.commit()?;

    let reader = index
        .reader_builder()
        .reload_policy(ReloadPolicy::Manual)
        .try_into()?;
    reader.reload()?;
    let searcher = reader.searcher();
    let query_parser = QueryParser::for_index(&index, vec![text]);
    let query = query_parser.parse_query("hello")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;

    assert_eq!(top_docs.len(), 1);
    let doc = searcher.doc::<TantivyDocument>(top_docs[0].1)?;
    assert_eq!(
        doc.get_first(text).and_then(|v| v.as_str()).unwrap_or(""),
        "hello world"
    );

    Ok(())
}
