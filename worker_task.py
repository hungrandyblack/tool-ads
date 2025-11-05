import time
import traceback
import tempfile
from pathlib import Path
from driver_utils import build_driver
from auth import login_flow
from actions import click_like
from config import CONFIG

def _unpack_task(task):
    if isinstance(task, dict):
        idx = task.get("index", 0)
        email = task.get("email") or task.get("username") or ""
        password = task.get("password") or task.get("pwd") or ""
        proxy = task.get("proxy")
        return idx, email, password, proxy
    elif isinstance(task, (list, tuple)):
        try:
            idx = int(task[0])
            email = task[1]
            password = task[2] if len(task) > 2 else ""
            proxy = None
            if len(task) >= 5:
                proxy = task[4]
            elif len(task) == 4:
                maybe = task[3]
                if isinstance(maybe, str) and (":" in maybe or "." in maybe):
                    proxy = maybe
            return idx, email, password, proxy
        except Exception:
            return 0, "", "", None
    else:
        return 0, "", "", None


def _log(log_func, msg):
    try:
        if callable(log_func):
            log_func(msg)
        else:
            print(msg)
    except Exception:
        print(msg)


def worker_task(task, log_func=None):
    idx, email, password, proxy = _unpack_task(task)
    result = {"index": idx, "email": email, "success": False, "like": False, "error": None}

    _log(log_func, f"[{idx}] Bắt đầu: {email} (proxy={proxy})")

    driver = None
    try:
        temp_dir = Path(tempfile.gettempdir()) / f"multi_login_profile_{idx}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        driver = build_driver(
            instance_id=idx,
            headless=CONFIG.get("headless", False),
            user_data_dir=temp_dir,
            proxy=proxy,
            extra_args=CONFIG.get("additional_args", [])
        )
        driver.set_page_load_timeout(CONFIG.get("timeout", 30))

        # 🔹 Lấy IP hiện tại của Chrome
        try:
            driver.get("https://api.ipify.org")
            time.sleep(1)
            ip_info = driver.find_element("tag name", "body").text.strip()
            result["ip"] = ip_info
            _log(log_func, f"[{idx}] IP hiện tại: {ip_info}")
        except Exception as e:
            result["ip"] = f"Không lấy được IP ({e})"
            _log(log_func, f"[{idx}] Không lấy được IP: {e}")

        # 🔹 Mở trang login
        target = CONFIG.get("target_url")
        if target:
            _log(log_func, f"[{idx}] Mở {target}")
            driver.get(target)
            time.sleep(1)

        # 🔹 Login
        ok, msg = login_flow(driver, CONFIG, email, password, idx)
        _log(log_func, f"[{idx}] login result: {ok}, {msg}")
        result["success"] = bool(ok)

        # 🔹 Like nếu login thành công
        if ok:
            time.sleep(1)
            liked = click_like(driver, timeout=8, instance_id=idx)
            result["like"] = bool(liked)
            _log(log_func, f"[{idx}] click_like -> {liked}")

        # 🔹 Lưu cookie để debug (tùy chọn)
        try:
            import json
            cookies = driver.get_cookies()
            ck_path = Path(tempfile.gettempdir()) / f"cookies_{idx}.json"
            ck_path.write_text(json.dumps(cookies), encoding="utf-8")
        except Exception:
            pass

    except Exception as e:
        tb = traceback.format_exc()
        result["error"] = str(e)
        _log(log_func, f"[{idx}] Lỗi: {e}\n{tb}")

    finally:
        # 🔸 KHÔNG đóng trình duyệt để bạn kiểm tra bằng tay
        # Nếu sau này muốn bật lại, chỉ cần bỏ comment 2 dòng dưới
        # if driver:
        #     try:
        #         driver.quit()
        #     except Exception:
        #         pass
        pass

    _log(log_func, f"[{idx}] Kết thúc: {email} -> {result}")
    return result
