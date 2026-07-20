import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNNER = PROJECT_ROOT / "warehouse" / "scripts" / "run_offline_batch.ps1"
CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"
WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
DEPLOYMENT_DOC = PROJECT_ROOT / "docs" / "deployment-integration.md"
GITIGNORE = PROJECT_ROOT / ".gitignore"

EXPECTED_STAGES = [
    "crawler",
    "ods_check",
    "ods_ddl",
    "ods_load",
    "dwd",
    "ads",
    "mysql_export",
    "smoke_test",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_offline_batch_runner_exists_and_exposes_parameters():
    script = _read(RUNNER)

    assert "param(" in script
    assert "$batchdate" in script
    assert "validatepattern('^\\d{4}-\\d{2}-\\d{2}$')" in script
    for parameter in ("$startfrom", "$skipstages", "$logsroot", "$backendbaseurl", "$frontendbaseurl"):
        assert parameter in script


def test_offline_batch_runner_declares_expected_stage_order():
    script = _read(RUNNER)
    stage_match = re.search(r"\$stageorder\s*=\s*@\((.*?)\)", script, flags=re.DOTALL)
    assert stage_match is not None

    stages = re.findall(r"'([^']+)'", stage_match.group(1))
    assert stages == EXPECTED_STAGES


def test_offline_batch_runner_references_existing_pipeline_scripts():
    script = _read(RUNNER).replace("\\", "/")

    for expected in (
        "crawler/run.py",
        "warehouse/scripts/check_ods_inputs.ps1",
        "warehouse/hive/ods/create_ods_tables.sql",
        "warehouse/scripts/load_ods.ps1",
        "warehouse/scripts/run_dwd.ps1",
        "warehouse/scripts/run_ads.ps1",
        "warehouse/scripts/export_ads_mysql.ps1",
        "deploy/scripts/smoke_test.ps1",
    ):
        assert expected in script


def test_offline_batch_runner_writes_logs_and_summary():
    script = _read(RUNNER)

    assert "logs/offline-batch" in script
    assert "run-summary.json" in script
    for stage in EXPECTED_STAGES:
        assert f"{stage}.log" in script
    for status in ("success", "failed", "skipped", "not_run"):
        assert status in script


def test_foundation_check_and_gitignore_include_offline_batch_assets():
    check = _read(CHECK)
    gitignore = _read(GITIGNORE)

    assert "warehouse/scripts/run_offline_batch.ps1" in check
    assert "run-summary.json" in check
    assert "logs/offline-batch/" in gitignore


def test_docs_show_default_resume_and_skip_examples():
    docs = _read(WAREHOUSE_README) + "\n" + _read(DEPLOYMENT_DOC)

    assert "run_offline_batch.ps1" in docs
    assert "-startfrom dwd" in docs
    assert "-skipstages crawler,smoke_test" in docs
    assert "logs/offline-batch" in docs


def test_offline_batch_runner_captures_output_and_fails_fast():
    script = _read(RUNNER)

    assert "invoke-loggedstage" in script
    assert "start-process" in script
    assert "redirectstandardoutput" in script
    assert "redirectstandarderror" in script
    assert 'throw "offline batch failed at stage' in script
