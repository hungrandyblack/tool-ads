# worker_task.py
import time
import traceback
import tempfile
from pathlib import Path

# Các module bạn đã có trong project
from driver_utils import build_driver
from auth import login_flow
from actions import click_like
from config import CONFIG

def _unpack_task(task):
    """
    Hỗ trợ 2 kiểu task:
      - tuple: (i, email, pwd, CONFIG, proxy)
      - dict: {"index": i, "email":..., "password":..., "proxy": ...}
    Trả về (idx, email, password, proxy)
    """
    if isinstance(task, dict):
        idx = task.get("index", 0)
        email = task.get("email") or task.get("username") or ""
        password = task.get("password") or task.get("pwd") or ""
        proxy = task.get("proxy")
        return idx, email, password, proxy
    elif isinstance(task, (list, tuple)):
        # tolerant unpack: try to extract known positions
        try:
            idx = int(task[0])
            email = task[1]
            password = task[2] if len(task) > 2 else ""
            # task may contain config in pos 3 and proxy pos 4
            proxy = None
            if len(task) >= 5:
                proxy = task[4]
            elif len(task) == 4:
                # could be (i,email,pwd,proxy) or (i,email,pwd,CONFIG)
                maybe = task[3]
                if isinstance(maybe, str) and (":" in maybe or "." in maybe):
                    proxy = maybe
                else:
                    proxy = None
            return idx, email, password, proxy
        except Exception:
            # fallback: try best effort
            try:
                email = str(task[1])
                pwd = str(task[2]) if len(task) > 2 else ""
                return 0, email, pwd, None
            except Exception:
                return 0, "", "", None
    else:
        return 0, "", "", None


def _log(log_func, msg):
    """Ghi log: nếu GUI gửi log_func, dùng nó; nếu None, dùng print."""
    try:
        if callable(log_func):
            log_func(msg)
        else:
            print(msg)
    except Exception:
        print(msg)


def worker_task(task, log_func=None):
    """
    Thực thi 1 tác vụ: khởi Chrome, login, click like.
    - task có thể là tuple (i,email,pwd,CONFIG,proxy) như GUI tạo,
      hoặc dict {"index":..., "email":..., "password":..., "proxy": ...}
    - log_func: optional, hàm nhận 1 string để in lên GUI
    Trả về dict kết quả.
    """
    idx, email, password, proxy = _unpack_task(task)
    result = {"index": idx, "email": email, "success": False, "like": False, "error": None}

    _log(log_func, f"[{idx}] Bắt đầu: {email} (proxy={proxy})")

    driver = None
    try:
        # tạo user-data-dir riêng cho mỗi instance để tránh chồng session
        temp_dir = Path(tempfile.gettempdir()) / f"multi_login_profile_{idx}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # build driver (driver_utils.build_driver xử lý proxy string nếu cần)
        driver = build_driver(
            instance_id=idx,
            headless=CONFIG.get("headless", False),
            user_data_dir=temp_dir,
            proxy=proxy,
            extra_args=CONFIG.get("additional_args", [])
        )
        driver.set_page_load_timeout(CONFIG.get("timeout", 30))

        # mở trang login (nếu bạn muốn override URL, set CONFIG['target_url'])
        target = CONFIG.get("target_url")
        if target:
            _log(log_func, f"[{idx}] Mở {target}")
            driver.get(target)
            time.sleep(1)

        # gọi login_flow (auth.py) — login_flow trả (bool, message)
        ok, msg = login_flow(driver, CONFIG, email, password, idx)
        _log(log_func, f"[{idx}] login result: {ok}, {msg}")
        result["success"] = bool(ok)

        if ok:
            # chờ một chút nếu cần, sau đó click like bằng actions.click_like
            time.sleep(0.5)
            liked = click_like(driver, timeout=8, instance_id=idx)
            result["like"] = bool(liked)
            _log(log_func, f"[{idx}] click_like -> {liked}")

        # optional: lưu cookies để debug
        try:
            cookies = driver.get_cookies()
            ck_path = Path(tempfile.gettempdir()) / f"cookies_{idx}.json"
            import json
            ck_path.write_text(json.dumps(cookies), encoding="utf-8")
        except Exception:
            pass

    except Exception as e:
        tb = traceback.format_exc()
        result["error"] = str(e)
        _log(log_func, f"[{idx}] Lỗi: {e}\n{tb}")
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    _log(log_func, f"[{idx}] Kết thúc: {email} -> {result}")
    return result
