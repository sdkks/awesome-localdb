use redb::{Database, ReadableDatabase, ReadableTable, TableDefinition};

const TABLE: TableDefinition<&str, &str> = TableDefinition::new("kv");

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let db = Database::create("mydb.redb")?;
    let write_txn = db.begin_write()?;
    {
        let mut table = write_txn.open_table(TABLE)?;
        table.insert("greeting", "Hello from redb")?;
    }
    write_txn.commit()?;
    let read_txn = db.begin_read()?;
    let table = read_txn.open_table(TABLE)?;
    if let Some(entry) = table.get("greeting")? {
        println!("greeting = {}", entry.value());
    }
    Ok(())
}
