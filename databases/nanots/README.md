# NanoTS

> **Category:** time-series | **License:** Apache-2.0 | **Stars:** ~100

## Overview

NanoTS is a lightweight, high-performance embedded time-series database optimized for real-time streaming applications like video surveillance, finance, and IoT sensor data. It uses memory-mapped storage with lock-free data structures to deliver lightning-fast writes (8.83us on SSD, 113K+ writes/second) and sub-microsecond reads. Like SQLite, it runs entirely in-process with no server required.

## Quick Start

### Python

```python
# Install: pip install nanots
import nanots
import time
import json

# Allocate a fixed-size database: 64KB blocks, 100 blocks = ~6MB
nanots.allocate_file("sensors.nts", 64 * 1024, 100)

# Create a writer and a stream context
writer = nanots.Writer("sensors.nts")
wctx = writer.create_context("temperature", '{"unit": "celsius"}')

# Write 100 temperature readings — one per second
base = int(time.time() * 1000)
for i in range(100):
    data = json.dumps({"sensor": "A1", "temp_c": 22.0 + i * 0.1}).encode()
    writer.write(wctx, data, 0, base + i * 1000)

# Read data in a time range
reader = nanots.Reader("sensors.nts")
frames = reader.read("temperature", base, base + 50_000)
for f in frames[:5]:
    d = json.loads(f["data"].decode())
    print(f"ts={f['timestamp']}  temp={d['temp_c']}C  sensor={d['sensor']}")

# Iterate with timestamp seeking
it = nanots.Iterator("sensors.nts", "temperature")
it.find(base + 10_000)  # seek to first frame >= base + 10s
for f in it:
    d = json.loads(f["data"].decode())
    print(f"ts={f['timestamp']}  temp={d['temp_c']}C")
```

### Go

```go
package main

import (
    "fmt"
    "log"
    "time"

    "github.com/nanots/nanots-go"
)

func main() {
    // Allocate database: 1MB blocks, 10 blocks = 10MB
    err := nanots.AllocateFile("metrics.nts", 1024*1024, 10)
    if err != nil {
        log.Fatal(err)
    }

    // Write data with multiple streams
    writer, _ := nanots.NewWriter("metrics.nts", false)
    defer writer.Close()

    cpuCtx, _ := writer.CreateWriteContext("cpu/usage", `{"host": "server1"}`)
    memCtx, _ := writer.CreateWriteContext("mem/usage", `{"host": "server1"}`)
    defer cpuCtx.Close()
    defer memCtx.Close()

    ts := time.Now().UnixMilli()
    writer.Write(cpuCtx, []byte("45.2"), ts, 0)
    writer.Write(memCtx, []byte("2048"), ts, 0)

    // Read all frames in a time range
    reader, _ := nanots.NewReader("metrics.nts")
    defer reader.Close()

    reader.Read("cpu/usage", 0, ts, func(frame nanots.Frame) error {
        fmt.Printf("CPU: %s%% at %d\n", string(frame.Data), frame.Timestamp)
        return nil
    })

    // Seek to a specific timestamp with an iterator
    iter, _ := nanots.NewIterator("metrics.nts", "cpu/usage")
    defer iter.Close()

    if err := iter.Find(ts - 60000); err == nil && iter.Valid() {
        frame, _ := iter.Current()
        fmt.Printf("Found: %s at %d\n", string(frame.Data), frame.Timestamp)
    }

    // Discover available streams
    tags, _ := reader.QueryStreamTags(0, ts)
    fmt.Printf("Streams: %v\n", tags)
}
```

## On-Disk Format

Memory-Mapped Binary Blocks (single `.nts` file with SQLite metadata). Blocks contain a header, a frame index mapping `(timestamp, secondary_key)` to offsets, and variable-size frame data.

## Core Strengths

- 113,000+ writes/second sustained on SSD with lock-free storage
- Memory-mapped architecture enables sub-microsecond reads
- Pre-allocated storage eliminates disk-full surprises and fragmentation
- Multiple independent streams in a single file with separate write contexts
- Configurable block sizes for durability/performance trade-offs
- Auto-reclaim mode recycles oldest blocks when space runs out
- Composite (timestamp, secondary_key) ordering for non-unique timestamps
- Crash recovery with frame-level atomicity guarantees

## Best Use Cases

1. **Video surveillance** — Capture dozens of camera streams concurrently while reviewers scrub through history with frame-accurate seeking
2. **IoT sensor data** — High-frequency sensor readings with efficient time-based queries and analysis
3. **Financial tick data** — Trade data with microsecond precision, market data replay, low-latency historical queries
4. **Embedded robotics** — Lidar, IMU, GPS, and camera streams captured at native rates with precise time alignment
5. **Scientific data acquisition** — Multi-channel synchronized time-series at line rate with event-based window retrieval

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_time_series.py`](python/src/recipe_time_series.py) | Write sensor readings, query by time range, and iterate with seeking |

## Limitations & Caveats

- Each stream supports exactly one writer (unlimited concurrent readers per stream)
- Frames are write-once (immutable after writing) — no in-place updates
- The current on-disk format (v2) is not backwards-compatible with v1; requires re-writing data to migrate
- C++ native library; language bindings require compilation of the C++ core
- Pre-allocated files cannot shrink without manual compaction to a new file

## Further Reading

- [Official Website](https://nanots.io)
- [Source Repository](https://github.com/dicroce/nanots)
- [Benchmarks](https://github.com/dicroce/nanots_bench/blob/main/RESULTS.md)
- [Python Bindings](https://pypi.org/project/nanots/)
- [Go Bindings README](https://github.com/dicroce/nanots/tree/main/bindings/nanots-go)
