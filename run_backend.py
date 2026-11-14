import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Set PYTHONPATH for spawned uvicorn subprocesses/workers
os.environ["PYTHONPATH"] = str(backend_dir) + (os.pathsep + os.environ["PYTHONPATH"] if "PYTHONPATH" in os.environ else "")

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        app_dir=str(backend_dir),
    )
