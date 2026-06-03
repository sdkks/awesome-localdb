"""
Recipe: Time Series
Database: NanoTS
Description: Demonstrate NanoTS as an embedded time-series database for
             writing sensor readings, querying by time range, seeking
             with iterators, and discovering available streams.

Usage: python src/recipe_time_series.py
"""

import json
import os
import tempfile

import nanots


def main() -> None:
    """Write sensor readings, query in time ranges, and iterate with seeking."""
    tmpfile = os.path.join(tempfile.gettempdir(), "recipe_nanots.nts")

    try:
        # 1. Allocate a fixed-size database file (64KB blocks, 100 blocks = ~6MB)
        print("=== Allocating database ===")
        nanots.allocate_file(tmpfile, 64 * 1024, 100)
        print(f"Created: {tmpfile}")

        # 2. Create a writer and two stream contexts
        writer = nanots.Writer(tmpfile)
        temp_ctx = writer.create_context("temperature", '{"unit": "celsius"}')
        hum_ctx = writer.create_context("humidity", '{"unit": "percent"}')

        base_ts = 1700000000000  # fixed epoch ms base

        # Write 20 temperature readings (one every 5 seconds)
        print("\n=== Writing temperature data ===")
        for i in range(20):
            ts = base_ts + i * 5000
            temp = 20.0 + i * 0.5 + (i % 3) * 0.1
            payload = json.dumps({
                "sensor": "temp-01",
                "value_c": round(temp, 2),
            }).encode("utf-8")
            writer.write(temp_ctx, payload, 0, ts)
            print(f"  ts={ts}  temp={round(temp, 2)}C")

        # Write 10 humidity readings
        print("\n=== Writing humidity data ===")
        for i in range(10):
            ts = base_ts + i * 10000
            hum = 55.0 + i * 1.2
            payload = json.dumps({
                "sensor": "hum-01",
                "value_pct": round(hum, 1),
            }).encode("utf-8")
            writer.write(hum_ctx, payload, 0, ts)
            print(f"  ts={ts}  hum={round(hum, 1)}%  sensor=hum-01")

        # 3. Read a time range from the temperature stream
        print("\n=== Reading temperature range ===")
        reader = nanots.Reader(tmpfile)
        mid_start = base_ts + 25_000
        mid_end = base_ts + 75_000
        frames = reader.read("temperature", mid_start, mid_end)
        print(f"Frames in range [{mid_start}, {mid_end}]: {len(frames)}")
        for f in frames[:5]:
            d = json.loads(f["data"].decode())
            print(f"  ts={f['timestamp']}  temp={d['value_c']}C  sensor={d['sensor']}")

        # 4. Use iterator to seek to a specific timestamp
        print("\n=== Iterator: seek to midpoint and iterate forward ===")
        it = nanots.Iterator(tmpfile, "temperature")
        it.find(base_ts + 50_000)
        count = 0
        for f in it:
            d = json.loads(f["data"].decode())
            print(f"  ts={f['timestamp']}  temp={d['value_c']}C")
            count += 1
            if count >= 5:
                break
        print(f"  (showing first {count} frames)")

        # 5. Discover available streams
        print("\n=== Stream discovery ===")
        tags = reader.query_stream_tags(base_ts, base_ts + 200_000)
        for tag_info in tags:
            print(f"  stream: {tag_info}")

        # Cleanup
        os.remove(tmpfile)
        print(f"\nCleaned up {tmpfile}")
        print("Done.")

    except ImportError:
        print("nanots package not installed. Install with: pip install nanots")
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
        raise


if __name__ == "__main__":
    main()
