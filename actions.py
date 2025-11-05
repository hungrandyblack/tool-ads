from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def click_like(driver, timeout=8, instance_id=0):
    """Find and click the like button near video-thumbup-line icon."""
    wait = WebDriverWait(driver, timeout)
    try:
        # Find button that has image alt 'video-thumbup-line'
        btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[.//img[contains(@alt,'video-thumbup-line')]]")
        ))
        driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(0.5)
        return True

    except Exception as e:
        # Fallback
        try:
            btn2 = driver.find_element(
                By.XPATH, "//button[contains(., 'Like') or contains(@class,'thumb')]"
            )
            driver.execute_script("arguments[0].click();", btn2)
            return True
        except Exception:
            return False