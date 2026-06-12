from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="DevDesk API", docs_url="/docs", openapi_url="/api/v1/openapi.json")

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
