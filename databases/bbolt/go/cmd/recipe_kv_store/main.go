// Package main demonstrates basic bbolt key/value operations: open, put, get,
// delete, and cursor-based iteration. It creates a temporary database, writes
// several key/value pairs, reads them back, iterates with a cursor, deletes a
// key, and verifies the deletion.
package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"

	bolt "go.etcd.io/bbolt"
)

func main() {
	// Create a temporary database file.
	tmpDir, err := os.MkdirTemp("", "bbolt-kv-store-*")
	if err != nil {
		log.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	dbPath := filepath.Join(tmpDir, "kvstore.db")
	fmt.Println("Database:", dbPath)

	// Open the database (creates if it does not exist).
	db, err := bolt.Open(dbPath, 0600, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Write key/value pairs in a read-write transaction.
	db.Update(func(tx *bolt.Tx) error {
		b, err := tx.CreateBucketIfNotExists([]byte("people"))
		if err != nil {
			return fmt.Errorf("create bucket: %w", err)
		}

		b.Put([]byte("alice"), []byte("engineer"))
		b.Put([]byte("bob"), []byte("designer"))
		b.Put([]byte("carol"), []byte("manager"))
		return nil
	})

	// Read a single key in a read-only transaction.
	db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("people"))
		if b == nil {
			return fmt.Errorf("bucket 'people' not found")
		}
		val := b.Get([]byte("alice"))
		fmt.Printf("alice: %s\n", val)
		return nil
	})

	// Iterate over all keys using a cursor.
	fmt.Println("All entries:")
	db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("people"))
		c := b.Cursor()
		for k, v := c.First(); k != nil; k, v = c.Next() {
			fmt.Printf("  %s -> %s\n", k, v)
		}
		return nil
	})

	// Delete a key.
	db.Update(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("people"))
		return b.Delete([]byte("bob"))
	})

	// Verify deletion.
	db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("people"))
		val := b.Get([]byte("bob"))
		if val == nil {
			fmt.Println("bob: deleted")
		} else {
			fmt.Printf("bob: %s\n", val)
		}
		return nil
	})

	fmt.Println("Done.")
}
