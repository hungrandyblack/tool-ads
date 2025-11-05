import requests

def load_accounts_from_api(api_url):
    try:
        print(f"Đang gọi API: {api_url}")
        res = requests.get(api_url, timeout=10)
        res.raise_for_status()
        data = res.json()

        # giả sử API trả về danh sách như:
        # [{"email": "...", "password": "...", "proxy": "..."}]
        accounts = []
        for item in data:
            email = item.get("email", "").strip()
            pwd = item.get("password", "").strip()
            proxy = item.get("proxy")
            if email:
                accounts.append((email, pwd, proxy))
        print(f"Đã tải {len(accounts)} tài khoản từ API")
        return accounts
    except Exception as e:
        print(f"Lỗi khi gọi API: {e}")
        return []
