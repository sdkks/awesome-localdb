package bbolt_test

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"

	bolt "go.etcd.io/bbolt"
)

// tempDB creates a temporary bbolt database and returns the *bolt.DB and a cleanup func.
func tempDB(t *testing.T) (*bolt.DB, func()) {
	t.Helper()
	dir, err := os.MkdirTemp("", "bbolt-test-*")
	if err != nil {
		t.Fatal(err)
	}

	path := filepath.Join(dir, "test.db")
	db, err := bolt.Open(path, 0600, nil)
	if err != nil {
		t.Fatal(err)
	}

	cleanup := func() {
		db.Close()
		os.RemoveAll(dir)
	}
	return db, cleanup
}

func TestCreateBucket(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	err := db.Update(func(tx *bolt.Tx) error {
		_, err := tx.CreateBucketIfNotExists([]byte("test-bucket"))
		return err
	})
	if err != nil {
		t.Fatalf("CreateBucketIfNotExists: %v", err)
	}

	db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("test-bucket"))
		if b == nil {
			t.Error("bucket should exist")
		}
		return nil
	})
}

func TestPutAndGet(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *bolt.Tx) error {
		b, err := tx.CreateBucketIfNotExists([]byte("data"))
		if err != nil {
			return err
		}
		return b.Put([]byte("key1"), []byte("value1"))
	})

	db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("data"))
		v := b.Get([]byte("key1"))
		if !bytes.Equal(v, []byte("value1")) {
			t.Errorf("expected 'value1', got %q", v)
		}
		return nil
	})
}

func TestDelete(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	bucket := []byte("data")
	key := []byte("deleteme")

	db.Update(func(tx *bolt.Tx) error {
		b, err := tx.CreateBucketIfNotExists(bucket)
		if err != nil {
			return err
		}
		return b.Put(key, []byte("val"))
	})

	db.Update(func(tx *bolt.Tx) error {
		b := tx.Bucket(bucket)
		return b.Delete(key)
	})

	db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket(bucket)
		v := b.Get(key)
		if v != nil {
			t.Errorf("key should be deleted, got %q", v)
		}
		return nil
	})
}

func TestCursorIteration(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	pairs := map[string]string{
		"a": "1",
		"b": "2",
		"c": "3",
	}

	db.Update(func(tx *bolt.Tx) error {
		b, err := tx.CreateBucketIfNotExists([]byte("items"))
		if err != nil {
			return err
		}
		for k, v := range pairs {
			if err := b.Put([]byte(k), []byte(v)); err != nil {
				return err
			}
		}
		return nil
	})

	db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("items"))
		c := b.Cursor()
		count := 0
		for k, v := c.First(); k != nil; k, v = c.Next() {
			expected, ok := pairs[string(k)]
			if !ok {
				t.Errorf("unexpected key: %s", k)
				continue
			}
			if string(v) != expected {
				t.Errorf("key %s: expected %s, got %s", k, expected, v)
			}
			count++
		}
		if count != len(pairs) {
			t.Errorf("expected %d keys, got %d", len(pairs), count)
		}
		return nil
	})
}

func TestNestedBuckets(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *bolt.Tx) error {
		parent, err := tx.CreateBucketIfNotExists([]byte("parent"))
		if err != nil {
			return err
		}
		child, err := parent.CreateBucketIfNotExists([]byte("child"))
		if err != nil {
			return err
		}
		return child.Put([]byte("nested-key"), []byte("nested-value"))
	})

	db.View(func(tx *bolt.Tx) error {
		parent := tx.Bucket([]byte("parent"))
		if parent == nil {
			t.Fatal("parent bucket not found")
		}
		child := parent.Bucket([]byte("child"))
		if child == nil {
			t.Fatal("child bucket not found")
		}
		v := child.Get([]byte("nested-key"))
		if !bytes.Equal(v, []byte("nested-value")) {
			t.Errorf("expected 'nested-value', got %q", v)
		}
		return nil
	})
}

func TestDeleteBucket(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *bolt.Tx) error {
		parent, err := tx.CreateBucketIfNotExists([]byte("parent"))
		if err != nil {
			return err
		}
		_, err = parent.CreateBucketIfNotExists([]byte("todelete"))
		return err
	})

	db.Update(func(tx *bolt.Tx) error {
		parent := tx.Bucket([]byte("parent"))
		return parent.DeleteBucket([]byte("todelete"))
	})

	db.View(func(tx *bolt.Tx) error {
		parent := tx.Bucket([]byte("parent"))
		b := parent.Bucket([]byte("todelete"))
		if b != nil {
			t.Error("bucket should have been deleted")
		}
		return nil
	})
}

func TestViewIsReadOnly(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	db.Update(func(tx *bolt.Tx) error {
		_, err := tx.CreateBucketIfNotExists([]byte("ro-bucket"))
		return err
	})

	// Attempting to write in a View transaction should panic/error.
	err := db.View(func(tx *bolt.Tx) error {
		b := tx.Bucket([]byte("ro-bucket"))
		return b.Put([]byte("key"), []byte("val"))
	})
	if err == nil {
		t.Error("expected error when writing in a read-only transaction")
	}
}
