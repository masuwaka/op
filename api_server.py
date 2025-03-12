import os
import signal
import subprocess
import sys

import psutil
import redis
import setproctitle
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

PROCESS_NAME = "project_api_server"
API_PORT = 50217
REDIS_PORT = 56379

app = FastAPI()


def check_duplicate_process():
    current_pid = os.getpid()
    setproctitle.setproctitle(PROCESS_NAME)

    try:
        result = subprocess.run(
            ["pgrep", "-x", PROCESS_NAME], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
        pids = [int(pid) for pid in result.stdout.strip().split("\n") if pid]
        if any(pid != current_pid for pid in pids):
            sys.exit(f"Other server process ({pids}) is already running.")
    except Exception:
        pass


def handle_signal(signum, frame):
    print(f"Signal {signum} received. Shutdown server.")
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 200:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "status": True})
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "status": False})


async def check_client_ip(request: Request):
    clientIP = request.client.host
    print(clientIP)
    allowedIPs = ["127.0.0.1"]
    #    client_ip = request.client.host
    #    allowed_ips = redis_client.smembers("allowed_ips")  # Redis から許可リスト取得
    if clientIP not in allowedIPs:
        raise HTTPException(status_code=403, detail="Access denied.")
    return clientIP


@app.get("/check/{pid}")
async def check_pid(pid: int, clientIP: str = Depends(check_client_ip)):
    if psutil.pid_exists(pid):
        return {"detail": f"PID({pid}) is running.", "status": True}
    return {"detail": f"PID({pid}) does not exist.", "status": False}


@app.post("/kill/{pid}")
async def kill_pid(pid: int, clientIP: str = Depends(check_client_ip)):
    try:
        process = psutil.Process(pid)
        process.terminate()
        return {"detail": f"PID({pid}) is terminated.", "status": True}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=200, detail=f"PID({pid}) is missing.")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail=f"No permission to kill PID({pid}).")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    check_duplicate_process()
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
