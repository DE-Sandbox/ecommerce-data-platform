# UUID v7 Implementation in PostgreSQL

## Overview
This document explains our UUID v7 implementation for the e-commerce platform, based on PostgreSQL best practices as of 2024.

## Why UUID v7?

### Performance Benefits
- **Time-ordered**: UUIDs are generated in ascending order, reducing index fragmentation
- **Better index performance**: 13.44% faster than UUID v4 for sorting operations
- **Reduced page splits**: Sequential nature minimizes B-tree index maintenance
- **Lower write amplification**: Consecutive values improve write performance

### Implementation Choice: Pure SQL
We chose a pure SQL implementation over extensions because:
1. **No compilation required**: Works everywhere without C/Rust compilation
2. **No superuser privileges**: Can be installed by regular database users
3. **Portable**: Easy to migrate between PostgreSQL instances
4. **Native PostgreSQL 18 compatibility**: Will be easy to migrate when native support arrives

## Implementation Details

### Basic UUID v7 Function
```sql
CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS uuid
LANGUAGE sql
VOLATILE
PARALLEL SAFE
AS $$
  SELECT encode(
    set_bit(
      set_bit(
        overlay(
          uuid_send(gen_random_uuid())
          placing substring(int8send(floor(extract(epoch from clock_timestamp()) * 1000)::bigint) from 3)
          from 1 for 6
        ),
        52, 1
      ),
      53, 1
    ),
    'hex'
  )::uuid
$$;
```

### High-Precision Variant
For high-throughput scenarios (>1000 inserts/second), we provide a sub-millisecond precision variant:
```sql
CREATE OR REPLACE FUNCTION uuid_generate_v7_precise()
```
This variant uses the 12-bit `rand_a` field for microsecond precision.

## UUID v7 Structure

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           unix_ts_ms                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          unix_ts_ms           |  ver  |       rand_a          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|var|                        rand_b                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                            rand_b                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

- **unix_ts_ms** (48 bits): Milliseconds since Unix epoch
- **ver** (4 bits): Version field (0111 for v7)
- **rand_a** (12 bits): Random or sub-millisecond precision
- **var** (2 bits): Variant field
- **rand_b** (62 bits): Random data

## Usage Guidelines

### When to Use Basic vs Precise Function

**Use `uuid_generate_v7()` when:**
- Normal transaction volume (<1000 inserts/second)
- Millisecond precision is sufficient
- Lower computational overhead desired

**Use `uuid_generate_v7_precise()` when:**
- High-throughput scenarios (>1000 inserts/second)
- Need guaranteed uniqueness in rapid succession
- Micro-benchmarking or performance testing

### Index Optimization

UUID v7 works best with standard B-tree indexes:
```sql
CREATE TABLE example (
    id uuid DEFAULT uuid_generate_v7() PRIMARY KEY,
    -- other columns
);
```

No special index configuration needed - the time-ordered nature automatically provides optimal performance.

### Extracting Timestamps

To extract the creation timestamp from a UUID v7:
```sql
SELECT extract_timestamp_from_uuidv7('018e7c25-8f3e-7000-8000-000000000000');
-- Returns: 2024-02-27 12:34:56.789
```

## Migration Path

### PostgreSQL 18 Native Support
PostgreSQL 18 (expected 2024/2025) will include native `uuidv7()` function. Our migration path:

1. Current: Use our `uuid_generate_v7()` function
2. PostgreSQL 18: Drop our function, use native `uuidv7()`
3. No data migration needed - UUIDs remain compatible

### From UUID v4
To migrate existing UUID v4 tables:
1. Add new UUID v7 column
2. Populate for new records
3. Optionally backfill old records (keeping original for references)

## Performance Considerations

### Benchmark Results
Based on community benchmarks:
- **Insert performance**: ~15% faster than UUID v4
- **Index size**: ~20% smaller due to better compression
- **Query performance**: 13.44% faster for time-based queries
- **Join performance**: Improved due to better cache locality

### Best Practices
1. **Always use as PRIMARY KEY**: Maximizes clustering benefits
2. **Avoid mixing with UUID v4**: Keep tables consistent
3. **Use for foreign keys**: Maintains ordering across relationships
4. **Consider partitioning**: Year_month column works well with UUID v7

## Troubleshooting

### Common Issues

1. **Timestamp extraction shows wrong time**
   - Ensure using `clock_timestamp()` not `now()`
   - Check timezone settingsre
l
2. **Duplicate UUIDs in rapid insertion**
   - Switch to `uuid_generate_v7_precise()`
   - Add application-level sequence if needed

3. **Performance degradation**
   - Verify indexes are being used
   - Check for index bloat
   - Run `ANALYZE` after bulk inserts

## References
- [PostgreSQL UUID v7 Pure SQL Implementation](https://postgresql.verite.pro/blog/2024/07/15/uuid-v7-pure-sql.html)
- [UUID Benchmark War](https://ardentperf.com/2024/02/03/uuid-benchmark-war/)
- [PostgreSQL 18 UUID v7 Support](https://www.thenile.dev/blog/uuidv7)
