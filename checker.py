#!/usr/bin/env python3
"""
BUET Fee Due Checker — Multi-User Version
Reads all registered users from Google Sheets,
checks their fees, and sends Telegram alerts.
"""

import asyncio, os, time, json, logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from telegram import Bot
from sheets import get_all_users

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
URL       = "https://billpay.sonalibank.com.bd/BUET/Fee"

FEE_TYPES = [
    "Registration Fee(RF)",
    "Hall Fee(HF)",
    "Dining Fee(DF)",
    "Certificate Fee(CF)",
    "Job Application Fee(JF)",
    "Admission Application Fee(AD)",
]

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)


# ── Telegram ───────────────────────────────────────────────────────────────────
async def _send(chat_id: str, text: str):
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

def notify(chat_id: str, text: str):
    if not BOT_TOKEN:
        log.warning("BOT_TOKEN not set")
        return
    try:
        asyncio.run(_send(chat_id, text))
        log.info(f"  → Notified {chat_id}")
    except Exception as e:
        log.error(f"  → Telegram error for {chat_id}: {e}")


# ── Browser ────────────────────────────────────────────────────────────────────
def get_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts)
    except Exception:
        driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    return driver


# ── Check one fee for one user ─────────────────────────────────────────────────
def check_fee(driver, student_id: str, phone: str, fee_label: str) -> dict:
    result = {"fee_label": fee_label, "amount": None, "no_bill": False, "error": None}
    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 15)

        sid = wait.until(EC.presence_of_element_located((By.ID, "CheckModel_StudentID")))
        sid.clear()
        sid.send_keys(student_id)

        Select(driver.find_element(By.ID, "CheckModel_FeeName")).select_by_visible_text(fee_label)

        phone_el = driver.find_element(By.ID, "CheckModel_MobileNo")
        phone_el.clear()
        phone_el.send_keys(phone)

        driver.find_element(By.XPATH, "//input[@type='submit' and @value='Check']").click()

        try:
            due_el = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//input[@id='PayBillModel_Amount']")))
            amount_str = due_el.get_attribute("value").strip()
            result["amount"] = float(amount_str) if amount_str else 0.0
        except Exception:
            page = driver.page_source.lower()
            if "no bill" in page:
                result["no_bill"] = True
            else:
                result["error"] = "Could not read result"

    except Exception as e:
        result["error"] = str(e)
        log.error(f"  [{fee_label}] Error: {e}")
    return result


# ── Check all fees for one user ────────────────────────────────────────────────
def check_user(driver, user: dict) -> list:
    student_id = user["student_id"]
    phone      = user["phone"]
    dues       = []

    log.info(f"Checking student {student_id}...")
    for fee_label in FEE_TYPES:
        result = check_fee(driver, student_id, phone, fee_label)
        time.sleep(2)
        if result["error"]:
            log.warning(f"  [{fee_label}] Error: {result['error']}")
        elif result["no_bill"]:
            log.info(f"  [{fee_label}] No bill")
        elif result["amount"] and result["amount"] > 0:
            log.info(f"  [{fee_label}] DUE: {result['amount']} BDT ⚠️")
            dues.append(result)
        else:
            log.info(f"  [{fee_label}] No due")

    return dues


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    log.info(f"=== BUET Fee Check starting — {now} ===")

    users = get_all_users()
    active_users = [u for u in users if u.get("active", "TRUE") == "TRUE"]
    log.info(f"Total users: {len(users)} | Active: {len(active_users)}")

    if not active_users:
        log.info("No active users. Exiting.")
        return

    driver = get_driver()
    summary = []

    try:
        for user in active_users:
            dues = check_user(driver, user)

            if dues:
                lines = [
                    f"🔔 <b>BUET Fee Due Alert!</b>  [{now}]",
                    f"🆔 Student ID: {user['student_id']}\n"
                ]
                for d in dues:
                    lines.append(f"💰 <b>{d['fee_label']}</b>: {d['amount']:.2f} BDT")
                lines.append(f"\n🔗 Pay: {URL}")
                notify(user["chat_id"], "\n".join(lines))

            summary.append({
                "chat_id":    user["chat_id"],
                "student_id": user["student_id"],
                "dues_found": len(dues),
                "dues":       dues,
            })

            time.sleep(3)   # pause between users

    finally:
        driver.quit()

    with open("last_run.json", "w") as f:
        json.dump({"checked_at": now, "users_checked": len(active_users),
                   "summary": summary}, f, indent=2)
    log.info(f"=== Done. Checked {len(active_users)} users. ===")


if __name__ == "__main__":
    main()
