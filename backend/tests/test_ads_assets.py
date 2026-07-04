from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_project_file(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def test_backend_requirements_include_mysql_connector():
    requirements = read_project_file("backend/requirements.txt")

    assert "mysql-connector-python" in requirements


def test_backend_readme_documents_ads_api_setup_and_endpoints():
    readme = read_project_file("backend/README.md")

    required_text = [
        "FastAPI ADS API",
        "ADS_MYSQL_HOST",
        "/api/ads/overview",
        "/api/ads/products/rank",
        "warehouse/scripts/export_ads_mysql.ps1",
    ]

    for text in required_text:
        assert text in readme


def test_foundation_check_includes_ads_backend_files():
    check_script = read_project_file("deploy/scripts/check.ps1")

    required_paths = [
        "backend/README.md",
        "backend/app/config.py",
        "backend/app/database.py",
        "backend/app/ads/router.py",
        "backend/app/ads/service.py",
        "backend/app/ads/repository.py",
        "backend/app/ads/schemas.py",
        "backend/app/ads/errors.py",
    ]

    for path in required_paths:
        assert f'"{path}"' in check_script
