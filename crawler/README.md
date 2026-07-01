# Crawler

The crawler collects ecommerce data needed by the offline data warehouse.

## Data Source

By default, the crawler reads from DummyJSON:

- Products: `https://dummyjson.com/products`
- Carts: `https://dummyjson.com/carts`
- Users: `https://dummyjson.com/users`

## Install

From the project root, install crawler dependencies with:

```bash
python -m pip install -r crawler/requirements.txt
```

## Run A Batch

Run crawler batches from the project root:

```bash
python crawler/run.py --batch-date 2026-07-01
```

If `--batch-date` is omitted, the crawler uses the current local date.

## Outputs

Raw JSON files are written to:

```text
crawler/data/raw/<batch-date>/{products,carts,users}.json
```

Processed JSONL files are written to:

```text
crawler/data/processed/<batch-date>/{products,carts,users}.jsonl
```

The entire `crawler/data/` directory is ignored by Git, so generated crawler output is not committed.
