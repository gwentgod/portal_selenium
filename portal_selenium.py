from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC

PORTAL_URL = "https://hkuportal.hku.hk/login.html"

OPENING = "https://sis-main.hku.hk/cs/sisprod/cache/PS_CS_STATUS_OPEN_ICN_1.gif"
SUCCEED = "/cs/sisprod/cache/PS_CS_STATUS_SUCCESS_ICN_1.gif"

USERNAME = ""
PASSWORD = ""

REFRESH_RATE = 5
TIMEOUT = 30

options = Options()
options.add_argument('--headless')

driver = webdriver.Chrome(options=options)

while True:
    try:
        driver.get(PORTAL_URL)

        username_input = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#username")))
        password_input = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#password")))
        submit = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type=image]")))

        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)
        submit.click()

        add_class_link = WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#crefli_Z_HC_SSR_SSENRL_CART_LNK > a")))
        add_class_link.click()

        while True:
            frame = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#ptifrmtgtframe")))
            driver.switch_to.frame(frame)

            sem_2 = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[id^=SSR_DUMMY_RECV1]")))
            cont = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#win0divDERIVED_SSS_SCT_SSR_PB_GO input")))
            sem_2.click()
            cont.click()

            temporary_list = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="SSR_REGFORM_VW$scroll$0"]/tbody/tr[2]/td/table')))
            course_num = len(temporary_list.find_elements(By.CSS_SELECTOR, "tr")) - 1

            print("Refreshed at", datetime.now())
            for course in range(course_num):
                course_status = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located(
                    (By.XPATH, f'//*[@id="win0divDERIVED_REGFRM1_SSR_STATUS_LONG${course}"]/div/img'))).get_attribute(
                    "src")

                if course_status == OPENING:
                    proceed = WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, f'//*[@id="DERIVED_REGFRM1_LINK_ADD_ENRL$82$"]')))
                    proceed.click()

                    finish = WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#DERIVED_REGFRM1_SSR_PB_SUBMIT")))
                    finish.click()

                    result = WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, f'//*[@id="win0divDERIVED_REGFRM1_SSR_STATUS_LONG${course}"]/div/img'))).get_attribute("src")

                    if result == SUCCEED:
                        print("Course selection has been completed\7")
                        exit(0)
                    else:
                        print("Attempted selection but failed\7")
                        exit(1)

            sleep(REFRESH_RATE)
            driver.refresh()

    except TimeoutException:
        continue

    finally:
        driver.quit()
