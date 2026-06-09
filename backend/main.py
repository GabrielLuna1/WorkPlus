import asyncio
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import database
from core.logger import logger
from core.config import settings
from api.router import router

if sys.platform == "win32":
    loop_policy = asyncio.WindowsProactorEventLoopPolicy()
    asyncio.set_event_loop_policy(loop_policy)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("inicializando servico")

    if settings.email_imap_host:
        from services.email_manager import email_manager

        logger.info("email_manager.configurado", host=settings.email_imap_host)

    await database.connect()

    db = database.get_db()

    try:
        from core.scheduler import init_scheduler

        init_scheduler()
    except Exception as e:
        logger.warning("scheduler.init_erro", error=str(e))

    yield
    logger.info("fechando servico")

    try:
        from core.scheduler import stop_scheduler

        stop_scheduler()
    except Exception:
        pass

    await database.close()


app = FastAPI(title="WorkHunter API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
