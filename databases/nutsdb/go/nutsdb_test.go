package nutsdb_test

import (
	"os"
	"testing"

	"github.com/nutsdb/nutsdb"
)

// tempDB creates a temporary NutsDB database and returns the *nutsdb.DB and a
// cleanup func.
func tempDB(t *testing.T) (*nutsdb.DB, func()) {
	t.Helper()
	dir, err := os.MkdirTemp("", "nutsdb-test-*")
	if err != nil {
		t.Fatal(err)
	}

	db, err := nutsdb.Open(
		nutsdb.DefaultOptions,
		nutsdb.WithDir(dir),
	)
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

	err := db.Update(func(tx *nutsdb.Tx) error {
		return tx.NewBucket(nutsdb.DataStructureBTree, "test-bucket")
	})
	if err != nil {
		t.Fatalf("NewBucket: %v", err)
	}

	// Verify bucket exists by iterating buckets.
	db.View(func(tx *nutsdb.Tx) error {
		found := false
		err := tx.IterateBuckets(nutsdb.DataStructureBTree, "*", func(bucket string) bool {
			if bucket == "test-bucket" {
				found = true
				return false
			}
			return true
		})
		if err != nil {
			t.Fatalf("IterateBuckets: %v", err)
		}
		if !found {
			t.Error("bucket 'test-bucket' should exist")
		}
		return nil
	})
}

func TestPutAndGet(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	bucket := "data"

	db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewBucket(nutsdb.DataStructureBTree, bucket); err != nil {
			return err
		}
		return tx.Put(bucket, []byte("key1"), []byte("value1"), 0)
	})

	db.View(func(tx *nutsdb.Tx) error {
		val, err := tx.Get(bucket, []byte("key1"))
		if err != nil {
			t.Fatalf("Get: %v", err)
		}
		if string(val) != "value1" {
			t.Errorf("expected 'value1', got %q", val)
		}
		return nil
	})
}

func TestDelete(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	bucket := "data"
	key := []byte("deleteme")

	db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewBucket(nutsdb.DataStructureBTree, bucket); err != nil {
			return err
		}
		return tx.Put(bucket, key, []byte("val"), 0)
	})

	db.Update(func(tx *nutsdb.Tx) error {
		return tx.Delete(bucket, key)
	})

	db.View(func(tx *nutsdb.Tx) error {
		_, err := tx.Get(bucket, key)
		if err == nil {
			t.Error("key should be deleted but Get succeeded")
		}
		return nil
	})
}

func TestGetAllIteration(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	bucket := "items"

	pairs := map[string]string{
		"a": "1",
		"b": "2",
		"c": "3",
	}

	db.Update(func(tx *nutsdb.Tx) error {
		if err := tx.NewBucket(nutsdb.DataStructureBTree, bucket); err != nil {
			return err
		}
		for k, v := range pairs {
			if err := tx.Put(bucket, []byte(k), []byte(v), 0); err != nil {
				return err
			}
		}
		return nil
	})

	db.View(func(tx *nutsdb.Tx) error {
		keys, vals, err := tx.GetAll(bucket)
		if err != nil {
			t.Fatalf("GetAll: %v", err)
		}

		if len(keys) != 3 {
			t.Errorf("expected 3 entries, got %d", len(keys))
		}

		for i, key := range keys {
			expected, ok := pairs[string(key)]
			if !ok {
				t.Errorf("unexpected key: %s", key)
				continue
			}
			if string(vals[i]) != expected {
				t.Errorf("key %s: expected %s, got %s", key, expected, vals[i])
			}
		}
		return nil
	})
}

func TestDeleteBucket(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	bucket := "todelete"

	db.Update(func(tx *nutsdb.Tx) error {
		return tx.NewBucket(nutsdb.DataStructureBTree, bucket)
	})

	db.Update(func(tx *nutsdb.Tx) error {
		return tx.DeleteBucket(nutsdb.DataStructureBTree, bucket)
	})

	db.View(func(tx *nutsdb.Tx) error {
		found := false
		err := tx.IterateBuckets(nutsdb.DataStructureBTree, "*", func(b string) bool {
			if b == bucket {
				found = true
				return false
			}
			return true
		})
		if err != nil {
			t.Fatalf("IterateBuckets: %v", err)
		}
		if found {
			t.Error("bucket should have been deleted")
		}
		return nil
	})
}

func TestViewIsReadOnly(t *testing.T) {
	db, cleanup := tempDB(t)
	defer cleanup()

	bucket := "ro-bucket"

	db.Update(func(tx *nutsdb.Tx) error {
		return tx.NewBucket(nutsdb.DataStructureBTree, bucket)
	})

	// Attempting to write in a View transaction should fail.
	err := db.View(func(tx *nutsdb.Tx) error {
		return tx.Put(bucket, []byte("key"), []byte("val"), 0)
	})
	if err == nil {
		t.Error("expected error when writing in a read-only transaction")
	}
}
