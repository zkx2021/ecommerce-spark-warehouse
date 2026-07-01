from fastapi import FastAPI


app = FastAPI(title="Ecommerce Spark Warehouse API")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ecommerce-spark-warehouse-api"
    }
