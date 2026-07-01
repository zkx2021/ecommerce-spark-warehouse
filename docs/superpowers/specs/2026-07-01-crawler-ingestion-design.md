# Crawler Ingestion Design

## Goal

Build the second project phase: a runnable crawler ingestion module that fetches ecommerce-like data from DummyJSON, stores raw API payloads by batch date, and writes simple normalized JSONL files for later HDFS and Hive ingestion.

## Scope

This phase implements local crawler ingestion only. It does not upload files to HDFS, create Hive tables, run Spark jobs, or update the dashboard with real metrics. Those are later phases.

The accepted scope is:

- Fetch DummyJSON `products`, `carts`, and `users` sources from `crawler/config/sources.json`.
- Save raw API responses under `crawler/data/raw/<batch-date>/`.
- Save processed JSONL under `crawler/data/processed/<batch-date>/`.
- Use batch dates in `YYYY-MM-DD` format, defaulting to the current local date when not provided.
- Keep generated data out of Git.
- Provide tests that do not depend on real network access.

## Data Layout

For a run with `--batch-date 2026-07-01`, files are written as:

```text
crawler/data/raw/2026-07-01/products.json
crawler/data/raw/2026-07-01/carts.json
crawler/data/raw/2026-07-01/users.json
crawler/data/processed/2026-07-01/products.jsonl
crawler/data/processed/2026-07-01/carts.jsonl
crawler/data/processed/2026-07-01/users.jsonl
```

Raw files preserve the API response for each source. Processed files contain one JSON object per line.

## Architecture

The crawler module is a small Python package under `crawler/app/`.

- `crawler/app/config.py` reads and validates `crawler/config/sources.json`.
- `crawler/app/client.py` fetches JSON from each configured source.
- `crawler/app/transform.py` converts API response envelopes into entity rows.
- `crawler/app/storage.py` writes raw JSON and processed JSONL files.
- `crawler/app/runner.py` coordinates config loading, fetch, transform, and storage.
- `crawler/run.py` is the command-line entry point.

The implementation uses `requests` for HTTP. It keeps dependencies small and avoids heavier crawler frameworks because DummyJSON is an API source, not a dynamic website.

## Source Handling

Each source config entry has:

- `name`: output file stem, such as `products`.
- `url`: DummyJSON endpoint.
- `entity`: semantic entity name, such as `product`, `order`, or `user`.

The transformer expects the top-level DummyJSON payload to contain an array under the source name:

- `products` source reads `payload["products"]`.
- `carts` source reads `payload["carts"]`.
- `users` source reads `payload["users"]`.

Each output row includes:

- `entity`: source entity value.
- `source`: source name.
- `batch_date`: run batch date.
- `data`: original item object from DummyJSON.

This keeps the first processed format simple and stable for Hive ODS ingestion while preserving all source fields.

## Command-Line Interface

The command is:

```powershell
python crawler/run.py --batch-date 2026-07-01
```

If `--batch-date` is omitted, the runner uses the current local date. If it is present, it must match `YYYY-MM-DD`.

The command exits non-zero when:

- Source config is missing or invalid.
- Any HTTP request fails.
- A response cannot be parsed as JSON.
- A response does not contain the expected array for its source.
- Files cannot be written.

## Error Handling

HTTP requests use a finite timeout. Non-2xx responses and network errors are raised with source context so the failing source is clear.

The runner fails the whole batch on the first source error. It does not silently skip a source because downstream warehouse layers should not receive partial batches without an explicit retry decision.

Storage writes parent directories before writing files. JSON is written as UTF-8 with stable indentation for raw files and UTF-8 line-delimited JSON for processed files.

## Testing Strategy

Unit tests cover:

- Source config loading and validation.
- Batch date validation and defaulting behavior.
- Transforming DummyJSON envelopes into JSONL rows.
- Raw JSON and processed JSONL storage paths.
- Runner orchestration with a mocked HTTP client.

Tests must not call the real DummyJSON network endpoints. A manual verification command can call the real API after implementation:

```powershell
python crawler/run.py --batch-date 2026-07-01
```

## Success Criteria

- `python -m pytest crawler/tests -v` passes.
- `python crawler/run.py --batch-date 2026-07-01` writes the expected raw and processed files when network access is available.
- Generated `crawler/data/` files are not tracked by Git.
- The README documents how to run the crawler and what files it writes.

## Out Of Scope

- HDFS upload commands.
- Hive table DDL.
- Spark transformations.
- Scheduling and incremental retries.
- A real browser or HTML scraping crawler.
- Dashboard updates from processed data.
