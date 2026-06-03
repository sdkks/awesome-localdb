// Package main demonstrates basic buntdb key/value operations: open, set, get,
// delete, index creation and iteration, spatial queries, and TTL-based expiration.
// It uses an in-memory database for simplicity.
package main

import (
	"fmt"
	"log"
	"time"

	"github.com/tidwall/buntdb"
)

func main() {
	// Open an in-memory database.
	db, err := buntdb.Open(":memory:")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// ── Set key/value pairs ────────────────────────────────────────────

	db.Update(func(tx *buntdb.Tx) error {
		tx.Set("user:alice", "engineer", nil)
		tx.Set("user:bob", "designer", nil)
		tx.Set("user:carol", "manager", nil)
		return nil
	})

	// ── Get a single key ───────────────────────────────────────────────

	db.View(func(tx *buntdb.Tx) error {
		val, err := tx.Get("user:alice")
		if err != nil {
			return err
		}
		fmt.Printf("alice: %s\n", val)
		return nil
	})

	// ── Create a string index and iterate in ascending order ───────────

	db.CreateIndex("users", "user:*", buntdb.IndexString)

	fmt.Println("All users (ascending by value):")
	db.View(func(tx *buntdb.Tx) error {
		return tx.Ascend("users", func(key, value string) bool {
			fmt.Printf("  %s -> %s\n", key, value)
			return true
		})
	})

	// ── TTL-based expiration ───────────────────────────────────────────

	db.Update(func(tx *buntdb.Tx) error {
		tx.Set("temp:ephemeral", "gone-soon", &buntdb.SetOptions{
			Expires: true,
			TTL:     50 * time.Millisecond,
		})
		return nil
	})

	fmt.Println("temp:ephemeral set with 50ms TTL")
	time.Sleep(100 * time.Millisecond)

	db.View(func(tx *buntdb.Tx) error {
		_, err := tx.Get("temp:ephemeral")
		if err == buntdb.ErrNotFound {
			fmt.Println("temp:ephemeral: expired and removed")
		} else if err != nil {
			return err
		}
		return nil
	})

	// ── Spatial index example ──────────────────────────────────────────

	db.CreateSpatialIndex("fleet", "fleet:*:pos", buntdb.IndexRect)

	db.Update(func(tx *buntdb.Tx) error {
		tx.Set("fleet:car1:pos", buntdb.Point(33.0, -112.0), nil)  // Phoenix
		tx.Set("fleet:car2:pos", buntdb.Point(34.0, -118.0), nil)  // Los Angeles
		tx.Set("fleet:car3:pos", buntdb.Point(40.0, -74.0), nil)   // New York
		return nil
	})

	// Query vehicles within a bounding box (southwest US).
	fmt.Println("Vehicles in SW US bounding box:")
	db.View(func(tx *buntdb.Tx) error {
		return tx.Intersects("fleet", "[30 -120],[35 -110]", func(key, value string) bool {
			fmt.Printf("  %s at %s\n", key, value)
			return true
		})
	})

	// ── Delete a key ──────────────────────────────────────────────────

	db.Update(func(tx *buntdb.Tx) error {
		_, err := tx.Delete("user:bob")
		return err
	})

	db.View(func(tx *buntdb.Tx) error {
		val, err := tx.Get("user:bob")
		if err == buntdb.ErrNotFound {
			fmt.Println("bob: deleted")
		} else if err != nil {
			return err
		} else {
			fmt.Printf("bob: %s\n", val)
		}
		return nil
	})

	fmt.Println("Done.")
}
