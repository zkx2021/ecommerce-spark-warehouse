import argparse

from crawler.app.config import default_batch_date, load_sources, parse_batch_date
from crawler.app.runner import run_ingestion


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ecommerce crawler ingestion.")
    parser.add_argument("--batch-date", help="Batch date in YYYY-MM-DD format.")
    args = parser.parse_args()

    batch_date = parse_batch_date(args.batch_date) if args.batch_date else default_batch_date()
    sources = load_sources()
    results = run_ingestion(sources=sources, batch_date=batch_date)

    for source_name, result in results.items():
        print(
            f"{source_name}: rows={result['rows']} "
            f"raw={result['raw']} processed={result['processed']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
