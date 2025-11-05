import zipfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager


def parse_proxy_string(proxy_str):
    """
    Phân tích chuỗi proxy dạng:
    host:port hoặc host:port:user:pass
    Trả về tuple (host, port, user, pass)
    """
    if not proxy_str:
        return None
    parts = proxy_str.split(":")
    if len(parts) == 2:
        host, port = parts
        return host, port, None, None
    elif len(parts) >= 4:
        host, port, user, pwd = parts[:4]
        return host, port, user, pwd
    return None


def create_proxy_extension(instance_id, host, port, user, pwd):
    """
    Tạo file .zip extension để cấu hình proxy có user/pass.
    """
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "ProxyAuth",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        }
    }
    """

    background_js = f"""
    var config = {{
            mode: "fixed_servers",
            rules: {{
                singleProxy: {{
                    scheme: "http",
                    host: "{host}",
                    port: parseInt({port})
                }},
                bypassList: ["localhost"]
            }}
        }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});
    function callbackFn(details) {{
        return {{
            authCredentials: {{
                username: "{user}",
                password: "{pwd}"
            }}
        }};
    }}
    chrome.webRequest.onAuthRequired.addListener(
        callbackFn,
        {{urls: ["<all_urls>"]}},
        ['blocking']
    );
    """

    ext_dir = Path(Path.cwd()) / f"proxy_auth_{instance_id}.zip"
    with zipfile.ZipFile(ext_dir, 'w') as zp:
        zp.writestr("manifest.json", manifest_json.strip())
        zp.writestr("background.js", background_js.strip())
    return str(ext_dir)


def build_driver(instance_id, headless=False, user_data_dir=None, proxy=None, extra_args=None):
    """
    Tạo đối tượng Chrome WebDriver với cấu hình proxy + headless.
    """
    options = webdriver.ChromeOptions()

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    if user_data_dir:
        options.add_argument(f"--user-data-dir={str(user_data_dir)}")

    if extra_args:
        for a in extra_args:
            options.add_argument(a)

    parsed = parse_proxy_string(proxy)
    ext_zip = None

    if parsed:
        host, port, user, pwd = parsed
        if user and pwd:
            try:
                ext_zip = create_proxy_extension(instance_id, host, port, user, pwd)
                options.add_extension(ext_zip)
            except Exception as e:
                print(f"[{instance_id}] create_proxy_extension failed: {e}")
        else:
            options.add_argument(f"--proxy-server=http://{host}:{port}")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)

    try:
        driver = webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
        # cleanup extension file if exists
        if ext_zip and Path(ext_zip).exists():
            try:
                Path(ext_zip).unlink()
            except Exception:
                pass
        raise e

    # ẩn navigator.webdriver để tránh bị detect
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass

    return driver
