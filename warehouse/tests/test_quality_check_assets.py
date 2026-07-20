from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = PROJECT_ROOT / "warehouse" / "scripts" / "run_quality_check.ps1"
CHECKER = PROJECT_ROOT / "warehouse" / "scripts" / "quality_check.py"
FOUNDATION_CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"
RUNNER = PROJECT_ROOT / "warehouse" / "scripts" / "run_offline_batch.ps1"
WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
DEPLOYMENT_DOC = PROJECT_ROOT / "docs" / "deployment-integration.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_quality_check_wrapper_exists_and_calls_python_checker():
    script = _read(WRAPPER)

    assert "param(" in script
    assert "$batchdate" in script
    assert "$reportdir" in script
    assert "$processedroot" in script
    assert "$adsroot" in script
    assert "quality_check.py" in script
    assert "--batch-date" in script
    assert "--processed-root" in script
    assert "--ads-root" in script
    assert "--report-dir" in script
    assert "logs\\quality-check" in script


def test_foundation_check_includes_quality_check_assets():
    check = _read(FOUNDATION_CHECK)

    assert "warehouse/scripts/quality_check.py" in check
    assert "warehouse/scripts/run_quality_check.ps1" in check
    assert "quality-report.json" in check


def test_quality_checker_mentions_validation_not_cleaning():
    checker = _read(CHECKER)

    assert "quality" in checker
    assert "clean" not in checker


def test_offline_batch_runner_places_quality_check_before_smoke_test():
    runner = _read(RUNNER).replace("\\", "/")

    assert "'mysql_export', 'quality_check', 'smoke_test'" in runner
    assert "quality_check.log" in runner
    assert "warehouse/scripts/run_quality_check.ps1" in runner


def test_docs_explain_quality_check_is_not_cleaning():
    docs = _read(WAREHOUSE_README) + "\n" + _read(DEPLOYMENT_DOC)

    assert "quality_check" in docs
    assert "quality-report.json" in docs
    assert "not data cleaning" in docs
    assert "does not modify data" in docs
