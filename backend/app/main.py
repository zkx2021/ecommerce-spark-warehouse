from fastapi import FastAPI

from backend.app.ads.router import router as ads_router


app = FastAPI(title="Ecommerce Spark Warehouse API")
app.include_router(ads_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ecommerce-spark-warehouse-api"
    }
