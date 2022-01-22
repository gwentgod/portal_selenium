from time import sleep
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait, TimeoutException
from selenium.webdriver.support import expected_conditions as EC

PORTAL_URL = "https://hkuportal.hku.hk/login.html"

OPENING = "https://sis-main.hku.hk/cs/sisprod/cache/PS_CS_STATUS_OPEN_ICN_1.gif"
CLOSED = "https://sis-main.hku.hk/cs/sisprod/cache/PS_CS_STATUS_CLOSED_ICN_1.gif"
SUCCEED = "/cs/sisprod/cache/PS_CS_STATUS_SUCCESS_ICN_1.gif"

with open("pwd.txt", "r") as f:
    USERNAME, PASSWORD = f.read().split('\n')[:2]

REFRESH_RATE = 5 * 60
TIMEOUT = 30
MAX_REATTEMPTS = 10


options = Options()
options.headless = True

driver = webdriver.Firefox(options=options)

reattempts = 0

while reattempts < MAX_REATTEMPTS:
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

        while reattempts < MAX_REATTEMPTS:
            driver.refresh()

            frame = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#ptifrmtgtframe")))
            driver.switch_to.frame(frame)

            sem_2 = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[id^=SSR_DUMMY_RECV1]")))
            cont = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#win0divDERIVED_SSS_SCT_SSR_PB_GO input")))
            sem_2.click()
            cont.click()

            temporary_list = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="SSR_REGFORM_VW$scroll$0"]/tbody/tr[2]/td/table/tbody/tr')))[1:]

            print("Refreshed at", datetime.now())

            if temporary_list[0].find_element(By.CSS_SELECTOR, "div").get_attribute("id") == "win0divP_NO_CLASSES$0":
                print("No class in temporary list!\7")
                exit(0)

            for course in temporary_list:
                course_name = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[id^=P_CLASS_NAME]"))).text.split('\n')[0]
                course_status = WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[id^=win0divDERIVED_REGFRM1_SSR_STATUS_LONG] img"))).get_attribute("src")

                if course_status == OPENING:
                    print(course_name, "opening, selection proceeding\7")

                    proceed = WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, f'//*[@id="DERIVED_REGFRM1_LINK_ADD_ENRL$82$"]')))
                    proceed.click()
                    finish = WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#DERIVED_REGFRM1_SSR_PB_SUBMIT")))
                    finish.click()

                    result = WebDriverWait(driver, TIMEOUT).until(
                        EC.presence_of_element_located((By.XPATH, f'//*[@id="win0divDERIVED_REGFRM1_SSR_STATUS_LONG${course}"]/div/img'))).get_attribute("src")
                    if result == SUCCEED:
                        print("Selection has been completed")
                    else:
                        reattempts += 1
                        print(f"Attempted selection but failed. Retrying {reattempts}/{MAX_REATTEMPTS}\7")
                    continue

                elif course_status == CLOSED:
                    print(course_name, "is closed")

            reattempts = 0
            sleep(REFRESH_RATE)

    except Exception as e:
        reattempts += 1
        print(f"{e}\n{reattempts}/{MAX_REATTEMPTS}\7")
        continue

    finally:
        driver.quit()
