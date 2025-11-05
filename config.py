CONFIG = {
    # Đường dẫn tới Chrome driver nếu bạn dùng bản riêng
    "driver_path": "",  # để trống nếu dùng selenium-manager tự động

    # Thời gian chờ (giây)
    "timeout": 60,

    # Chạy ẩn hay không
    "headless": False,  # đặt False để thấy Chrome bật lên

    # Có bật extension proxy không
    "use_proxy_extension": True,

    # Thư mục lưu file extension proxy
    "proxy_dir": "proxy_auth_1.zip",  # hoặc proxy_auth_0.zip

    # URL cần login / thao tác (bạn đổi tùy project)
    "target_url": "https://thescoopz.com/c/truecrime",

    # Log chi tiết
    "debug": True,

    # Số lần retry khi thao tác lỗi
    "max_retries": 2,
}
