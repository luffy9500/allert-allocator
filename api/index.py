# Entrypoint Vercel — re-esporta l'app FastAPI dal package backend.
# Vercel cerca "app" in api/index.py (tra i percorsi standard supportati).
from backend.main import app  # noqa: F401
