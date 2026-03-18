from fastapi import FastAPI, Header, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import secrets
import socket
from uuid import uuid4
from typing import Optional

import psutil
import pyqrcode
import uvicorn

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
ENV_FILE = os.path.join(BASE_DIR, ".env")
ALLOWED_MODES = {"private", "public"}
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_env_file(path: str) -> None:
    if not os.path.isfile(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_env_file(ENV_FILE)

APP_MODE = os.getenv("APP_MODE", "private").strip().lower()
UPLOAD_TOKEN = os.getenv("UPLOAD_TOKEN", "").strip()
ALLOW_FILE_OVERWRITE = _is_truthy(os.getenv("ALLOW_FILE_OVERWRITE", "false"))

if APP_MODE not in ALLOWED_MODES:
    raise RuntimeError("APP_MODE invalido. Use 'private' ou 'public'.")

if APP_MODE == "private" and not UPLOAD_TOKEN:
    raise RuntimeError("Modo private ativo, mas UPLOAD_TOKEN nao foi definido no arquivo .env.")


def _is_valid_ipv4(address: str) -> bool:
    return bool(address) and not address.startswith("127.") and not address.startswith("169.254.")


def detect_local_ip() -> str:
    interfaces = psutil.net_if_addrs()

    for preferred_name in ("Wi-Fi", "Ethernet"):
        for addr in interfaces.get(preferred_name, []):
            if addr.family == socket.AF_INET and _is_valid_ipv4(addr.address):
                return addr.address

    for addrs in interfaces.values():
        for addr in addrs:
            if addr.family == socket.AF_INET and _is_valid_ipv4(addr.address):
                return addr.address

    return socket.gethostbyname(socket.gethostname())


ip = detect_local_ip()


def auth_required() -> bool:
    return APP_MODE == "private"


def validate_upload_token(received_token: Optional[str]) -> None:
    if not auth_required():
        return

    if not received_token or not secrets.compare_digest(received_token, UPLOAD_TOKEN):
        raise HTTPException(status_code=401, detail="Token invalido")


def generate_qrcode() -> None:
    url = f"http://{ip}:8000"
    qr = pyqrcode.create(url)
    print(qr.terminal(quiet_zone=1))
    print(f"Acesse: {url}")
    if auth_required():
        print("Modo: private (senha obrigatoria)")
    else:
        print("Modo: public (sem senha)")


def _build_target_path(filename: str) -> str:
    target_path = os.path.join(UPLOAD_DIR, filename)
    if ALLOW_FILE_OVERWRITE or not os.path.exists(target_path):
        return target_path

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    unique_name = f"{stem}_{uuid4().hex[:8]}{suffix}"
    return os.path.join(UPLOAD_DIR, unique_name)


@app.get("/app/config")
def app_config():
    return {
        "mode": APP_MODE,
        "auth_required": auth_required(),
    }


@app.middleware("http")
async def disable_cache_for_core_paths(request, call_next):
    response = await call_next(request)
    if request.url.path in {"/", "/index.html", "/app/config"}:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.post("/file/upload")
async def uploadfile(file: UploadFile, x_upload_token: Optional[str] = Header(default=None)):
    validate_upload_token(x_upload_token)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo invalido")

    filename = Path(file.filename).name.strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Arquivo invalido")

    chunk_size = 1024 * 1024
    save_file_path = _build_target_path(filename)
    temp_file_path = f"{save_file_path}.part"

    try:
        with open(temp_file_path, "wb") as f:
            while True:
                chunk = await file.read(chunk_size)

                if not chunk:
                    break

                f.write(chunk)

        os.replace(temp_file_path, save_file_path)
        return {"filename": Path(save_file_path).name, "status": "Arquivo transferido com sucesso!"}
    except HTTPException:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise
    except OSError:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail="Erro ao salvar o arquivo")
    except Exception:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail="Erro ao transferir o arquivo")
    finally:
        await file.close()


if not os.path.isdir(STATIC_DIR):
    STATIC_DIR = BASE_DIR

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    generate_qrcode()
    uvicorn.run(app, host="0.0.0.0", port=8000)
