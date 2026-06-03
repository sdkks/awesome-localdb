package buntdb_test

import (
	"testing"
	"time"

	"github.com/tidwall/buntdb"
)

// tempDB creates an in-memory buntdb database and returns the *buntdb.DB and a cleanup func.
func tempDB(t *testing.T) (*buntdb.DB, func()) {
	t.Helper()
	db, err := buntdb.Open(":memory:")
	if err != nil {
		t.Fatal(err)
	}
	cleanup := func() {
		db.Close()
	}
	return db, cleanup
}

func TestSetAndGet(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *buntdb.Tx) error {
		_, _, err := tx.Set("key1", "value1", nil)
		return err
	})

	db.View(func(tx *buntdb.Tx) error {
		val, err := tx.Get("key1")
		if err != nil {
			t.Fatalf("Get key1: %v", err)
		}
		if val != "value1" {
			t.Errorf("expected 'value1', got %q", val)
		}
		return nil
	})
}

func TestDelete(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *buntdb.Tx) error {
		_, _, err := tx.Set("deleteme", "val", nil)
		return err
	})

	db.Update(func(tx *buntdb.Tx) error {
		_, err := tx.Delete("deleteme")
		return err
	})

	db.View(func(tx *buntdb.Tx) error {
		_, err := tx.Get("deleteme")
		if err != buntdb.ErrNotFound {
			t.Errorf("expected ErrNotFound after delete, got %v", err)
		}
		return nil
	})
}

func TestIndexIteration(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *buntdb.Tx) error {
		tx.Set("user:alice", "engineer", nil)
		tx.Set("user:bob", "designer", nil)
		tx.Set("user:carol", "manager", nil)
		return nil
	})

	err := db.CreateIndex("users", "user:*", buntdb.IndexString)
	if err != nil {
		t.Fatalf("CreateIndex: %v", err)
	}

	count := 0
	db.View(func(tx *buntdb.Tx) error {
		return tx.Ascend("users", func(key, value string) bool {
			count++
			return true
		})
	})

	if count != 3 {
		t.Errorf("expected 3 entries in index, got %d", count)
	}
}

func TestTTL(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *buntdb.Tx) error {
		_, _, err := tx.Set("temp", "val", &buntdb.SetOptions{
			Expires: true,
			TTL:     50 * time.Millisecond,
		})
		return err
	})

	// Wait for expiry.
	time.Sleep(100 * time.Millisecond)

	db.View(func(tx *buntdb.Tx) error {
		_, err := tx.Get("temp")
		if err != buntdb.ErrNotFound {
			t.Errorf("expected ErrNotFound after TTL expiry, got %v", err)
		}
		return nil
	})
}

func TestSpatialIndex(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	err := db.CreateSpatialIndex("fleet", "fleet:*:pos", buntdb.IndexRect)
	if err != nil {
		t.Fatalf("CreateSpatialIndex: %v", err)
	}

	db.Update(func(tx *buntdb.Tx) error {
		tx.Set("fleet:car1:pos", buntdb.Point(33.0, -112.0), nil)
		tx.Set("fleet:car2:pos", buntdb.Point(34.0, -118.0), nil)
		return nil
	})

	count := 0
	db.View(func(tx *buntdb.Tx) error {
		return tx.Intersects("fleet", "[30 -120],[35 -110]", func(key, value string) bool {
			count++
			return true
		})
	})

	if count != 2 {
		t.Errorf("expected 2 vehicles in bounding box, got %d", count)
	}
}

func TestDescend(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *buntdb.Tx) error {
		tx.Set("item:a", "1", nil)
		tx.Set("item:b", "2", nil)
		tx.Set("item:c", "3", nil)
		return nil
	})

	err := db.CreateIndex("items", "item:*", buntdb.IndexString)
	if err != nil {
		t.Fatalf("CreateIndex: %v", err)
	}

	var keys []string
	db.View(func(tx *buntdb.Tx) error {
		return tx.Descend("items", func(key, value string) bool {
			keys = append(keys, key)
			return true
		})
	})

	if len(keys) != 3 {
		t.Errorf("expected 3 keys in descending order, got %d", len(keys))
	}
	if keys[0] != "item:c" {
		t.Errorf("expected first key 'item:c' in descending order, got %q", keys[0])
	}
}
