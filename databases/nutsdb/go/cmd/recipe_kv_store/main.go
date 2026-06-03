// Package main demonstrates basic NutsDB key/value operations: open, bucket
// creation, put, get, delete, and iteration. It creates a temporary database,
// writes several key/value pairs, reads them back, iterates over entries,
// deletes a key, and verifies the deletion.
package main

import (
	"fmt"
	"log"
	"os"

	"github.com/nutsdb/nutsdb"
)

func main() {
	// Create a temporary directory for the database.
	tmpDir, err := os.MkdirTemp("", "nutsdb-kv-store-*")
	if err != nil {
		log.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	fmt.Println("Database:", tmpDir)

	// Open the database (creates if it does not exist).
	db, err := nutsdb.Open(
		nutsdb.DefaultOptions,
		nutsdb.WithDir(tmpDir),
	)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	bucket := "people"

	// Create the bucket and write key/value pairs in a read-write transaction.
	if err := db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewBucket(nutsdb.DataStructureBTree, bucket); err != nil {
			return fmt.Errorf("create bucket: %w", err)
		}

		tx.Put(bucket, []byte("alice"), []byte("engineer"), 0)
		tx.Put(bucket, []byte("bob"), []byte("designer"), 0)
		tx.Put(bucket, []byte("carol"), []byte("manager"), 0)
		return nil
	}); err != nil {
		log.Fatal(err)
	}

	// Read a single key in a read-only transaction.
	if err := db.View(func(tx *nutsdb.Tx) error {
		val, err := tx.Get(bucket, []byte("alice"))
		if err != nil {
			return fmt.Errorf("get alice: %w", err)
		}
		fmt.Printf("alice: %s\n", val)
		return nil
	}); err != nil {
		log.Fatal(err)
	}

	// Iterate over all entries.
	fmt.Println("All entries:")
	if err := db.View(func(tx *nutsdb.Tx) error {
		keys, vals, err := tx.GetAll(bucket)
		if err != nil {
			return fmt.Errorf("getall: %w", err)
		}
		for i, key := range keys {
			fmt.Printf("  %s -> %s\n", key, vals[i])
		}
		return nil
	}); err != nil {
		log.Fatal(err)
	}

	// Delete a key.
	if err := db.Update(func(tx *nutsdb.Tx) error {
		return tx.Delete(bucket, []byte("bob"))
	}); err != nil {
		log.Fatal(err)
	}

	// Verify deletion.
	if err := db.View(func(tx *nutsdb.Tx) error {
		_, err := tx.Get(bucket, []byte("bob"))
		if err != nil {
			fmt.Println("bob: deleted")
		} else {
			fmt.Println("bob: still exists (unexpected)")
		}
		return nil
	}); err != nil {
		log.Fatal(err)
	}

	fmt.Println("Done.")
}
