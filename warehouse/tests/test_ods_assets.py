import json
import subprocess
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ODS_SQL = PROJECT_ROOT / "warehouse" / "hive" / "ods" / "create_ods_tables.sql"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def test_ods_sql_defines_expected_external_tables():
    sql = _read(ODS_SQL)

    for table_name in ("ods_products", "ods_carts", "ods_users"):
        assert f"create external table if not exists {table_name}" in sql


def test_ods_sql_uses_expected_columns_and_dt_partition():
    sql = _read(ODS_SQL)

    for column in ("entity string", "source string", "batch_date string", "data string"):
        assert column in sql
    assert "partitioned by (dt string)" in sql


def test_ods_sql_points_to_expected_hdfs_locations():
    sql = _read(ODS_SQL)

    assert "location '/warehouse/ecommerce/ods/products'" in sql
    assert "location '/warehouse/ecommerce/ods/carts'" in sql
    assert "location '/warehouse/ecommerce/ods/users'" in sql


CHECK_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "check_ods_inputs.ps1"


def test_check_ods_inputs_script_validates_all_sources():
    script = _read(CHECK_SCRIPT)

    assert "param(" in script
    assert "$batchdate" in script
    for source in ("products", "carts", "users"):
        assert f'"{source}"' in script
        assert f'{source}.jsonl' in script
    assert "crawler" in script
    assert "data" in script
    assert "processed" in script


LOAD_SCRIPT = PROJECT_ROOT / "warehouse" / "scripts" / "load_ods.ps1"


def test_load_ods_script_uses_expected_hdfs_partition_paths():
    script = _read(LOAD_SCRIPT)

    assert "/warehouse/ecommerce/ods" in script
    assert "dt=$batchdate" in script
    for source in ("products", "carts", "users"):
        assert f'"{source}"' in script
        assert f"{source}.jsonl" in script


def test_load_ods_script_registers_hive_partitions():
    script = _read(LOAD_SCRIPT)

    assert "partitionsqlprefix" not in script
    assert "alter table $table add if not exists partition" in script
    for table_name in ("ods_products", "ods_carts", "ods_users"):
        assert f'table = "{table_name}"' in script
        assert f"alter table {table_name} add if not exists partition" in script
    assert "invoke-compose -composeargs" in script


def test_load_ods_script_checks_native_command_failures():
    script = _read(LOAD_SCRIPT)

    assert "function invoke-native" in script
    assert "$lastexitcode" in script
    assert "throw" in script


def test_load_ods_script_binds_docker_compose_to_project_root():
    script = _read(LOAD_SCRIPT)

    assert "--project-directory" in script
    assert "$projectroot" in script
    assert "valuefromremainingarguments" not in script


def test_load_ods_script_invokes_compose_with_named_argument_arrays():
    script = _read(LOAD_SCRIPT)

    expected_calls = (
        'invoke-compose -composeargs @("exec", "namenode", "mkdir", "-p", $containertmpdir)',
        'invoke-compose -composeargs @("exec", "namenode", "hdfs", "dfs", "-mkdir", "-p", $hdfsdir)',
        'invoke-compose -composeargs @("cp", $localpath, "namenode:$containertmppath")',
        'invoke-compose -composeargs @("exec", "namenode", "hdfs", "dfs", "-put", "-f", $containertmppath, $hdfspath)',
        'invoke-compose -composeargs @("exec", "hive-server2", "beeline", "-u", "jdbc:hive2://localhost:10000", "-e", $partitionsql)',
        'invoke-compose -composeargs @("exec", "namenode", "rm", "-rf", $containertmpdir)',
    )

    for expected_call in expected_calls:
        assert expected_call in script


def test_invoke_compose_preserves_dash_prefixed_native_arguments():
    powershell = textwrap.dedent(
        r"""
        $ErrorActionPreference = "Stop"
        $projectRoot = "D:\repo"
        $script:Captured = @()

        function Invoke-Native {
          param(
            [Parameter(Mandatory = $true)]
            [string]$FilePath,

            [Parameter(Mandatory = $true)]
            [string[]]$Arguments
          )

          $script:Captured += [pscustomobject]@{
            FilePath = $FilePath
            Arguments = @($Arguments)
          }
        }

        function Invoke-Compose {
          param(
            [Parameter(Mandatory = $true)]
            [string[]]$ComposeArgs
          )

          Invoke-Native -FilePath "docker" -Arguments (@("compose", "--project-directory", $projectRoot) + $ComposeArgs)
        }

        Invoke-Compose -ComposeArgs @("exec", "namenode", "mkdir", "-p", "/tmp/ods-test")
        Invoke-Compose -ComposeArgs @("exec", "namenode", "hdfs", "dfs", "-put", "-f", "/tmp/ods-test/products.jsonl", "/warehouse/ecommerce/ods/products/dt=1999-01-01/products.jsonl")
        Invoke-Compose -ComposeArgs @("exec", "hive-server2", "beeline", "-u", "jdbc:hive2://localhost:10000", "-e", "ALTER TABLE ods_products ADD IF NOT EXISTS PARTITION (dt='1999-01-01')")

        $script:Captured | ConvertTo-Json -Depth 8 -Compress
        """
    )

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell],
        check=True,
        capture_output=True,
        text=True,
    )
    captured = json.loads(result.stdout)
    arguments = [entry["Arguments"] for entry in captured]

    assert arguments[0] == [
        "compose",
        "--project-directory",
        "D:\\repo",
        "exec",
        "namenode",
        "mkdir",
        "-p",
        "/tmp/ods-test",
    ]
    assert arguments[1][-4:] == [
        "-put",
        "-f",
        "/tmp/ods-test/products.jsonl",
        "/warehouse/ecommerce/ods/products/dt=1999-01-01/products.jsonl",
    ]
    assert arguments[2][-4:] == [
        "-u",
        "jdbc:hive2://localhost:10000",
        "-e",
        "ALTER TABLE ods_products ADD IF NOT EXISTS PARTITION (dt='1999-01-01')",
    ]


def test_load_ods_script_uses_unique_container_tmp_dir_and_finally_cleanup():
    script = _read(LOAD_SCRIPT)

    assert "$runid" in script
    assert "/tmp/$runid" in script
    assert "finally" in script


WAREHOUSE_README = PROJECT_ROOT / "warehouse" / "README.md"
FOUNDATION_CHECK = PROJECT_ROOT / "deploy" / "scripts" / "check.ps1"


def test_warehouse_readme_documents_ods_flow():
    readme = _read(WAREHOUSE_README)
    raw_readme = WAREHOUSE_README.read_text(encoding="utf-8")

    assert "ods" in readme
    assert "python crawler/run.py --batch-date 2026-07-01" in readme
    assert "check_ods_inputs.ps1" in readme
    assert "docker compose exec -T hive-server2" in raw_readme
    assert "beeline" in readme
    assert "create_ods_tables.sql" in readme
    assert "get-content -raw warehouse/hive/ods/create_ods_tables.sql" in readme
    assert "/workspace/warehouse/hive/ods/create_ods_tables.sql" not in readme
    assert "load_ods.ps1" in readme
    assert "/warehouse/ecommerce/ods" in readme


def test_foundation_check_includes_ods_assets():
    script = _read(FOUNDATION_CHECK)

    assert "warehouse/hive/ods/create_ods_tables.sql" in script
    assert "warehouse/scripts/check_ods_inputs.ps1" in script
    assert "warehouse/scripts/load_ods.ps1" in script
