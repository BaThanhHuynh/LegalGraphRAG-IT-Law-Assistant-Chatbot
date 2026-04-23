"""
FastAPI app entry point for IT Law Chatbot.
"""
import warnings
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import Config
from app.core.logger import logger
from app.api.routes.chat import chat_router

warnings.filterwarnings("ignore", category=FutureWarning)


def create_app():
    app = FastAPI(
        title="IT Law Chatbot API",
        description="API for consulting IT laws in Vietnam",
        version="1.0.0"
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": "Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau."},
        )

    # Include routers
    app.include_router(chat_router)

    # Serve static files at root (css, js, images, etc.)
    # This must be after the router to not shadow API routes
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

    return app


app = create_app()

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  IT Law Chatbot - Tư vấn Luật Công nghệ thông tin")
    print(f"  Server running at http://localhost:{Config.API_PORT}")
    print(f"{'='*60}\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=Config.API_PORT,
        reload=Config.API_DEBUG
    )

