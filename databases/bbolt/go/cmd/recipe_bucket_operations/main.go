// Package main demonstrates bbolt's nested bucket feature for logical
// key-space partitioning and namespace management. It creates a hierarchy
// of buckets, writes data into each, iterates over top-level buckets,
// lists keys within a nested bucket, and deletes a bucket.
package main

import (
	"fmt"
	"log"
	"os"
	"path/filepath"

	bolt "go.etcd.io/bbolt"
)

func main() {
	tmpDir, err := os.MkdirTemp("", "bbolt-buckets-*")
	if err != nil {
		log.Fatal(err)
	}
	defer os.RemoveAll(tmpDir)

	dbPath := filepath.Join(tmpDir, "buckets.db")
	fmt.Println("Database:", dbPath)

	db, err := bolt.Open(dbPath, 0600, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Create a hierarchy of buckets with nested sub-buckets.
	db.Update(func(tx *bolt.Tx) error {
		// Top-level bucket for projects.
		projects, err := tx.CreateBucketIfNotExists([]byte("projects"))
		if err != nil {
			return err
		}

		// Nested bucket for project-alpha.
		alpha, err := projects.CreateBucketIfNotExists([]byte("project-alpha"))
		if err != nil {
			return err
		}
		alpha.Put([]byte("lead"), []byte("alice"))
		alpha.Put([]byte("status"), []byte("active"))
		alpha.Put([]byte("priority"), []byte("high"))

		// Nested bucket for project-beta.
		beta, err := projects.CreateBucketIfNotExists([]byte("project-beta"))
		if err != nil {
			return err
		}
		beta.Put([]byte("lead"), []byte("bob"))
		beta.Put([]byte("status"), []byte("planning"))

		// Another top-level bucket for global settings.
		settings, err := tx.CreateBucketIfNotExists([]byte("settings"))
		if err != nil {
			return err
		}
		settings.Put([]byte("theme"), []byte("dark"))
		settings.Put([]byte("language"), []byte("en"))
		return nil
	})

	// List top-level buckets.
	fmt.Println("Top-level buckets:")
	db.View(func(tx *bolt.Tx) error {
		return tx.ForEach(func(name []byte, b *bolt.Bucket) error {
			fmt.Printf("  [%s]\n", name)
			return nil
		})
	})

	// Iterate over nested buckets inside 'projects'.
	fmt.Println("\nProjects:")
	db.View(func(tx *bolt.Tx) error {
		projects := tx.Bucket([]byte("projects"))
		if projects == nil {
			return nil
		}
		return projects.ForEach(func(k, v []byte) error {
			if v == nil {
				// v is nil for sub-buckets.
				fmt.Printf("  [%s] (bucket)\n", k)
				sub := projects.Bucket(k)
				if sub != nil {
					sub.ForEach(func(sk, sv []byte) error {
						fmt.Printf("    %s: %s\n", sk, sv)
						return nil
					})
				}
			} else {
				fmt.Printf("  %s: %s\n", k, v)
			}
			return nil
		})
	})

	// Read a value from a nested bucket directly.
	db.View(func(tx *bolt.Tx) error {
		projects := tx.Bucket([]byte("projects"))
		if projects == nil {
			return nil
		}
		alpha := projects.Bucket([]byte("project-alpha"))
		if alpha == nil {
			return nil
		}
		lead := alpha.Get([]byte("lead"))
		fmt.Printf("\nproject-alpha lead: %s\n", lead)
		return nil
	})

	// Delete a nested bucket.
	db.Update(func(tx *bolt.Tx) error {
		projects := tx.Bucket([]byte("projects"))
		if projects == nil {
			return nil
		}
		return projects.DeleteBucket([]byte("project-beta"))
	})
	fmt.Println("\nDeleted project-beta bucket.")

	// Verify the bucket was deleted.
	db.View(func(tx *bolt.Tx) error {
		projects := tx.Bucket([]byte("projects"))
		if projects.Bucket([]byte("project-beta")) == nil {
			fmt.Println("project-beta: no longer exists")
		}
		return nil
	})

	fmt.Println("Done.")
}
