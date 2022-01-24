from time import sleep
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

PORTAL_URL = "https://hkuportal.hku.hk/login.html"

OPENING = "https://sis-main.hku.hk/cs/sisprod/cache/PS_CS_STATUS_OPEN_ICN_1.gif"
CLOSED = "https://sis-main.hku.hk/cs/sisprod/cache/PS_CS_STATUS_CLOSED_ICN_1.gif"
SUCCEED = "https://sis-main.hku.hk/cs/sisprod/cache/PS_CS_STATUS_SUCCESS_ICN_1.gif"
FAILED = "https://sis-main.hku.hk/cs/sisprod/cache/PS_CS_STATUS_ERROR_ICN_1.gif"

with open("pwd.txt", "r") as f:
    USERNAME, PASSWORD = f.read().split('\n')[:2]

REFRESH_RATE = 5 * 60
TIMEOUT = 30
MAX_REATTEMPTS = 3
MAX_REFRESHES = 3


class Enrollee:
    def __init__(self):
        options = Options()
        options.headless = True
        self.driver = webdriver.Firefox(options=options)
        self.driver.get(PORTAL_URL)

        username_input = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#username")))
        password_input = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#password")))
        submit = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[type=image]")))

        username_input.send_keys(USERNAME)
        password_input.send_keys(PASSWORD)
        submit.click()

        add_class_link = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#crefli_Z_HC_SSR_SSENRL_CART_LNK > a")))
        add_class_link.click()

    def __del__(self):
        try:
            self.driver.quit()
        except:
            pass

    def proceed(self):
        proceed = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.XPATH, f'//*[@id="DERIVED_REGFRM1_LINK_ADD_ENRL$82$"]')))
        proceed.click()
        finish = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#DERIVED_REGFRM1_SSR_PB_SUBMIT")))
        finish.click()

        results = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_all_elements_located(
            (By.XPATH, '//*[@id="SSR_SS_ERD_ER$scroll$0"]/tbody/tr/td/table/tbody/tr')))
        results = results[1:]

        print(datetime.now())
        all_failed = True
        for result in results:
            result_name = WebDriverWait(result, TIMEOUT).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[id^=win0divR_CLASS_NAME] > span"))).text
            result_message = WebDriverWait(result, TIMEOUT).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[id^=win0divDERIVED_REGFRM1_SS_MESSAGE_LONG] > div"))).text
            result_status = WebDriverWait(result, TIMEOUT).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[id^=win0divDERIVED_REGFRM1_SSR_STATUS_LONG] img"))).get_attribute(
                "src")

            if result_status == SUCCEED:
                print(f"{result_name} Submitted for approval")
                all_failed = False
            elif result_status == FAILED:
                print(f"Unable to add {result_name}:\n{result_message}")

        if all_failed:
            print("Retrying")
            return 1

        return 0

    def check_status(self):
        self.driver.refresh()

        frame = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#ptifrmtgtframe")))
        self.driver.switch_to.frame(frame)

        sem_2 = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "input[id^=SSR_DUMMY_RECV1]")))
        cont = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#win0divDERIVED_SSS_SCT_SSR_PB_GO input")))
        sem_2.click()
        cont.click()

        temporary_list = WebDriverWait(self.driver, TIMEOUT).until(EC.presence_of_all_elements_located(
            (By.XPATH, '//*[@id="SSR_REGFORM_VW$scroll$0"]/tbody/tr[2]/td/table/tbody/tr')))
        temporary_list = temporary_list[1:]

        print("Refreshed at", datetime.now())

        if temporary_list[0].find_element(By.CSS_SELECTOR, "div").get_attribute("id") == "win0divP_NO_CLASSES$0":
            print("No class in temporary list")
            exit(0)

        for course in temporary_list:
            course_name = WebDriverWait(course, TIMEOUT).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[id^=P_CLASS_NAME]"))).text.split('\n')[0]
            course_status = WebDriverWait(course, TIMEOUT).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[id^=win0divDERIVED_REGFRM1_SSR_STATUS_LONG] img"))).get_attribute("src")

            if course_status == OPENING:
                print(course_name, "opening, selection proceeding\7")
                enrol_result = self.proceed()
                return enrol_result

            elif course_status == CLOSED:
                print(course_name, "is closed")

        return 2


def main():
    reattempts = 0
    while True:
        try:
            enrollee = Enrollee()

            refreshes = 0
            while refreshes < MAX_REFRESHES:
                check_result = enrollee.check_status()
                if check_result == 2:
                    refreshes = 0
                    print(f"Will refresh in {REFRESH_RATE} seconds")
                    sleep(REFRESH_RATE)
                elif check_result == 1:
                    refreshes += 1
                    continue

                reattempts = 0

            raise Exception("Reached maximum refreshes")

        except Exception as e:
            reattempts += 1
            del enrollee

            if reattempts > MAX_REATTEMPTS:
                print(f"Reached maximum reattempts, will retry in {REFRESH_RATE} seconds\7")
                sleep(REFRESH_RATE)
            sleep(1)

            print(f"{e}\nRestarting webdriver {reattempts}/{MAX_REATTEMPTS}")
            continue


if __name__ == "__main__":
    main()
