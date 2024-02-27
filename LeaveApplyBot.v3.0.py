from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
import time
from datetime import datetime, timedelta
from enum import Enum

app = Flask(__name__)


class LeaveType(Enum):
    DayLeave = 3
    NightLeave = 1
    DayLeaveExt = 6
    NightLeaveExt = 7


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/apply_leave', methods=['POST'])
def apply_leave():
    leave_type = int(request.form['leave_type'])
    leave_days = None
    if leave_type == 2 or leave_type == 4:
        leave_days = int(request.form['leave_days'])

    leave_type = actual_leave_type(leave_type)
    # Opening FireFox

    # Uncomment the below if you have custom path to the webdriver
    # service = Service(executable_path="path to geckodriver")
    # options = webdriver.FirefoxOptions()
    # driver = webdriver.Firefox(service=service, options=options)

    driver = webdriver.Firefox()

    # loging in first landing page (LPU requires login twice)
    driver.get("https://ums.lpu.in/lpuums")
    username_box = driver.find_element(By.NAME, "txtU")
    password_box = driver.find_element(By.NAME, 'TxtpwdAutoId_8767')

    student_reg_id = request.form['student_reg_id']
    student_password = request.form['student_password']

    username_box.send_keys(student_reg_id)
    password_box.send_keys(Keys.RETURN)
    password_box.send_keys(student_password)
    password_box.send_keys(Keys.RETURN)
    print_to_web("Initial login [success]")

    # Secondary(Main) Login page
    time.sleep(5)
    password_box = driver.find_element(By.NAME, 'TxtpwdAutoId_8767')
    password_box.send_keys(student_password)
    password_box.send_keys(Keys.RETURN)
    print("Main login [Success]")

    # Applying leave
    apply_leave_process(driver, leave_type, leave_days)

    return "Leave applied successfully!"


def apply_leave_process(driver, leave_type, leave_days):
    # Checking for popup message
    check_pop_up(driver)
    # Connecting to Leave Page
    time.sleep(3)
    driver.get(
        "https://ums.lpu.in/lpuums/frmStudentHostelLeaveApplicationTermWise.aspx")
    print("Accessing leave page [Success]")

    # Checking it for one more time
    check_pop_up(driver)

    # Selecting Term
    select_leave_term(driver)

    # Selecting Leave Type
    select_leave_type(driver, leave_type, leave_days)

    # Selecting Leave Time
    select_leave_time(driver)

    # Select Reason to Leave
    select_leave_reason(driver, leave_type)

    # Selecting Visit Place
    select_visit_place(driver, leave_type)

    # Select Staying Place
    select_stay_place(driver, leave_type)

    # Select Relative Phone Number
    select_relative_ph_no(driver)

    # Selecting Leave date and time 2nd time because it will go after refreshing
    select_leave_time(driver)

    # Selecting Returning time
    select_return_time(driver, leave_type, leave_days)

    # Click Leave button
    click_leave_time(driver)

    click_leave_reason(driver)

    time.sleep(2)
    # Selecting Returning time
    select_return_time(driver, leave_type, leave_days)

    click_return_time(driver)

    click_leave_reason(driver)

    # Submit button
    try:
        submit_button = driver.find_element(
            By.ID, "ctl00_cphHeading_btnSubmit")
        submit_button.click()
        print("Leave application: [Success]")
    except:
        print("Leave application: [Failed]")


def sl(f=5):
    time.sleep(f)


def actual_leave_type(leave_type):
    if leave_type == 1:
        leave_type = 3
    elif leave_type == 2:
        leave_type = 1
    elif leave_type == 3:
        leave_type = 6
    elif leave_type == 4:
        leave_type = 7
    return leave_type


def print_to_web(msg):
    print(msg)
    return msg


def check_pop_up(driver):
    time.sleep(5)
    try:
        print("Checking for pop up notifications")
        check_box = driver.find_element(By.ID, "chkReadMessage")
        check_box.click()

        confirm_button = driver.find_element(By.ID, "btnClose")
        confirm_button.click()
        print("PopUp Notifications cleared")

    except:
        print("PopUp Notifications not found.")
    return ("popup checked")


def select_leave_term(driver):
    try:
        leave_term_dropdown = driver.find_element(
            By.ID, "ctl00_cphHeading_ddlLeaveTerm")
        select_leave_term = Select(leave_term_dropdown)
        select_leave_term.select_by_value("Term-II")
        print("Select Leave Term: [Success]")

    except:
        print("Select Leave Term: [Failed]")

    return ("term selected")


def select_leave_type(driver, leave_type, leave_days):
    try:
        leave_type_dropdown = driver.find_element(
            By.ID, "ctl00_cphHeading_drpLeaveType")
        select_leave_type = Select(leave_type_dropdown)
        select_leave_type.select_by_value(str(leave_type))
        print("Select Leave Type: [Success]")

    except:
        print("Select Leave Type: [Failed]")


def select_leave_time(driver):
    try:
        leaving_time = create_leave_time()
        date_of_leaving = driver.find_element(
            By.ID, "ctl00_cphHeading_startdateRadDateTimePicker1_dateInput")
        driver.execute_script(
            "arguments[0].removeAttribute('readonly')", date_of_leaving)
        driver.execute_script(
            f"arguments[0].value = '{leaving_time}'", date_of_leaving)
        driver.execute_script(
            "arguments[0].setAttribute('class', 'riTextBox riRead')", date_of_leaving)
        print("Select Leave Time: [Success]")

    except:
        print("Select Leave Time: [Failed]")


def create_leave_time():
    unix_time = int(time.time())
    unix_time += 330*60
    nearest_time_slot = 15 - ((unix_time // 60) % 15)
    unix_time += nearest_time_slot * 60
    next_time_slot = datetime.utcfromtimestamp(unix_time)
    next_time_slot = next_time_slot.strftime('%H:%M %p')
    date = datetime.now()
    date = date.strftime('%m/%d/%Y')
    return date + " " + next_time_slot


def select_leave_reason(driver, leave_type):
    if leave_type == 3 or leave_type == 6:
        leave_reason = "For lunch"
    elif leave_type == 1 or leave_type == 7:
        leave_reason = "For movie and dinner after that"
    try:
        reason_for_leave = driver.find_element(
            By.ID, "ctl00_cphHeading_txtLeaveReason")
        reason_for_leave.send_keys(f"{leave_reason}")
        print("Select Leave Reason: [Success]")

    except:
        print("Select Leaving Reason: [Failed]")


def select_visit_place(driver, leave_type):
    visit_place = create_visit_place(leave_type)
    try:
        visit_place_dropdown = driver.find_element(
            By.ID, "ctl00_cphHeading_ddlVisitDay")
        select_visit_place = Select(visit_place_dropdown)
        select_visit_place.select_by_value(visit_place)
        print("Select Visit Place: [Success]")

    except:
        print("Select Visit Place: [Failed]")


def create_visit_place(leave_type):
    if leave_type == LeaveType.DayLeave.value:
        return "Local Visit"
    elif leave_type == LeaveType.DayLeaveExt.value:
        return "Phagwara"
    elif leave_type == LeaveType.NightLeave.value:
        return "Other"
    elif leave_type == LeaveType.NightLeaveExt.value:
        return "Other"


def select_stay_place(driver, leave_type):
    print("leave typevalue= ", leave_type, type(leave_type))
    if leave_type == 3 or leave_type == 6:
        print("day leave")
        stay_address = "Will come back to hostel"
    elif leave_type == 1 or leave_type == 7:
        print("night leave")
        stay_address = "Phagwara PG near Sabji Mandi"
    try:
        stay_place = driver.find_element(
            By.ID, "ctl00_cphHeading_txtPlaceToVisit")
        stay_place.send_keys("Phagwara near sabji mandi")
        print(stay_address)
        print("Select Stay Place: [Success]")

    except:
        print("Select Stay Place: [Failed]")


def select_relative_ph_no(driver):
    try:
        relative_ph_no = driver.find_element(
            By.ID, "ctl00_cphHeading_txtVisitingMobile")
        relative_ph_no.send_keys("9341498723")
        print("Select Relative Phone Number: [Success]")

    except:
        print("Select Relative Phone Number: [Failed]")


def select_return_time(driver, leave_type, leave_days):
    return_time = create_return_time(leave_type, leave_days)
    try:
        date_of_returning = driver.find_element(
            By.ID, "ctl00_cphHeading_enddateRadDateTimePicker2_dateInput")
        driver.execute_script(
            "arguments[0].removeAttribute('readonly')", date_of_returning)
        driver.execute_script(
            f"arguments[0].value = '{return_time}'", date_of_returning)
        driver.execute_script(
            "arguments[0].setAttribute('class', 'riTextBox riRead')", date_of_returning)
        print("Select Return Time: [Success]")

    except:
        print("Select Return Time: [Failed]")


def create_return_time(leave_type, leave_days):
    if (leave_type == LeaveType.DayLeave.value):
        today = datetime.now().date()
        today = today.strftime('%m/%d/%Y')
        return_time = today + " 06:45 PM"

    elif (leave_type == LeaveType.DayLeaveExt.value):
        today = datetime.now().date()
        today = today.strftime('%m/%d/%Y')
        return_time = today + " 09:45 PM"

    elif (leave_type == LeaveType.NightLeave.value):
        today = datetime.now().date()
        today = today + timedelta(days=int(leave_days))
        today = today.strftime('%m/%d/%Y')
        return_time = today + " 06:45 PM"

    elif (leave_type == LeaveType.NightLeaveExt.value):
        today = datetime.now().date()
        today = today + timedelta(days=int(leave_days))
        today = today.strftime('%m/%d/%Y')
        return_time = today + " 09:45 PM"

    return return_time


def click_leave_time(driver):
    try:
        time.sleep(1)
        date_of_returning = driver.find_element(
            By.ID, "ctl00_cphHeading_startdateRadDateTimePicker1_dateInput")
        date_of_returning.click()

    except:
        print("Debug: Leave time not pressed")


def click_return_time(driver):
    try:
        time.sleep(1)
        date_of_returning = driver.find_element(
            By.ID, "ctl00_cphHeading_enddateRadDateTimePicker2_dateInput")
        date_of_returning.click()

    except:
        print("Debug: Leave time not pressed")


def click_leave_reason(driver):
    try:
        time.sleep(1)
        reason_for_leave = driver.find_element(
            By.ID, "ctl00_cphHeading_txtLeaveReason")
        reason_for_leave.click()

    except:
        print("Debug: Reason box not clicked")


if __name__ == '__main__':
    app.run(debug=True, port=9001)
