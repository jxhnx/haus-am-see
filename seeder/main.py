from fastapi import FastAPI, Query
from fastapi.concurrency import run_in_threadpool
from seed import seed_initial_data, seed_single_record
from logging_config import setup_logging
import asyncio
import logging
from contextlib import asynccontextmanager

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.ingestion_task = None
    logger.info("Seeder app started")
    yield
    if app.state.ingestion_task and not app.state.ingestion_task.done():
        app.state.ingestion_task.cancel()
        logger.info("Seeder ingestion task cancelled on shutdown")

app = FastAPI(lifespan=lifespan)

@app.post("/seed/full")
async def full_load(
    count: int = Query(10_000),
    batch_size: int = Query(1000)
):
    await run_in_threadpool(seed_initial_data, count, batch_size)
    return {
        "status": "success",
        "records_created": count,
        "batch_size": batch_size
    }


@app.post("/seed/start")
async def start_ingestion(rate: float = Query(1.0)):
    if app.state.ingestion_task and not app.state.ingestion_task.done():
        logger.warning("Ingestion already running.")
        return {"status": "already running"}

    logger.info(f"Starting ingestion loop at {rate:.2f} batch/sec")

    async def ingest_loop():
        count = 0
        last_log = asyncio.get_event_loop().time()

        try:
            while True:
                seed_single_record()
                count += 1

                now = asyncio.get_event_loop().time()
                if now - last_log >= 10:
                    logger.info(f"Ingested {count} records.")
                    last_log = now

                await asyncio.sleep(1 / rate)

        except asyncio.CancelledError:
            logger.info("Ingestion loop stopped.")
            raise

    app.state.ingestion_task = asyncio.create_task(ingest_loop())
    return {"status": "started", "rate": rate}


@app.post("/seed/stop")
async def stop_ingestion():
    if app.state.ingestion_task and not app.state.ingestion_task.done():
        app.state.ingestion_task.cancel()
        logger.info("Ingestion task cancelled by user.")
        return {"status": "stopped"}

    logger.warning("No ingestion task running.")
    return {"status": "not running"}

@app.get("/healthz")
def healthz():
    status = {
        "app": "ok",
        "ingestion_running": bool(
            app.state.ingestion_task and not app.state.ingestion_task.done()
        )
    }
    return status
