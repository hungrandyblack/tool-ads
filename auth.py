import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def login_flow(driver, cfg, email, password, instance_id):
    wait = WebDriverWait(driver, 15)

    # 1️⃣ Click nút Sign in
    try:
        sign_in_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'Sign in') or contains(text(), 'Sign In')]")
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", sign_in_btn)
        driver.execute_script("arguments[0].click();", sign_in_btn)
        print(f"[{instance_id}] Clicked Sign in button")
    except Exception as e:
        print(f"[{instance_id}] Không tìm thấy nút Sign in: {e}")
        return False, "no_signin_button"

    # 2️⃣ Đợi popup hiện ra
    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//input[contains(@type,'email') or contains(@placeholder,'Email')]")
        ))
        print(f"[{instance_id}] Popup đăng nhập hiển thị")
    except Exception:
        print(f"[{instance_id}] Không thấy popup hoặc input đăng nhập")
        return False, "no_popup"

    # 3️⃣ Nhập email và password
    try:
        u = driver.find_element(By.XPATH, "//input[contains(@type,'email') or contains(@placeholder,'Email')]")
        p = driver.find_element(By.XPATH, "//input[contains(@type,'password')]")

        u.clear()
        u.send_keys(email)
        if p:
            p.clear()
            p.send_keys(password)
    except Exception as e:
        print(f"[{instance_id}] Lỗi nhập email/password: {e}")
        return False, "input_error"

    # 4️⃣ Click nút Continue (đúng nút form)
    try:
        submit = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//form//button[normalize-space()='Continue' and not(contains(., 'with'))]"
        )))
        driver.execute_script("arguments[0].click();", submit)
        print(f"[{instance_id}] Clicked Continue button (email-password)")
    except Exception as e:
        print(f"[{instance_id}] Không thấy hoặc không click được nút Continue: {e}")
        return False, "no_continue"

    # 5️⃣ Đợi login hoàn tất (popup đóng hoặc URL thay đổi)
    old_url = driver.current_url
    success = False
    try:
        # Đợi popup biến mất (ô email không còn hiển thị)
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@type,'email') or contains(@placeholder,'Email')]"))
        )
        success = True
    except Exception:
        # Nếu popup vẫn mở, thử xem URL có thay đổi không
        time.sleep(3)
        if driver.current_url != old_url:
            success = True

    if success:
        print(f"[{instance_id}] ✅ Đăng nhập thành công (popup đóng hoặc URL đổi)")
        return True, "ok"
    else:
        print(f"[{instance_id}] ❌ Hết thời gian chờ, popup vẫn mở hoặc URL không đổi")
        return False, "no_confirmation"
