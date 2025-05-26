from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException
import os
import time

# Set up download directory
current_path = os.getcwd()
download_dir = os.path.join(current_path, "testdata")

# Configure Chrome options
chrome_options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,  # Set download directory
    "plugins.always_open_pdf_externally": True,  # Download PDFs instead of opening
    "download.prompt_for_download": False        # Disable download prompt
}
chrome_options.add_experimental_option("prefs", prefs)

# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)

# Open the page
driver.get("https://web-as.tamu.edu/gradereports/")  # Replace with the actual URL

# Fetch year options
year_dropdown = Select(driver.find_element(By.ID, "ctl00_plcMain_lstGradYear"))
year_options = [option.text for option in year_dropdown.options]

# Iterate through years
for year in year_options:
    # Refresh year dropdown and select current year
    year_dropdown = Select(driver.find_element(By.ID, "ctl00_plcMain_lstGradYear"))
    year_dropdown.select_by_visible_text(year)

    # Fetch semester options
    semester_dropdown = Select(driver.find_element(By.ID, "ctl00_plcMain_lstGradTerm"))
    semester_options = [option.text for option in semester_dropdown.options]

    # Iterate through semesters
    for semester in semester_options:
        # Refresh semester dropdown and select current semester
        semester_dropdown = Select(driver.find_element(By.ID, "ctl00_plcMain_lstGradTerm"))
        semester_dropdown.select_by_visible_text(semester)

        # Fetch college options
        college_dropdown = Select(driver.find_element(By.ID, "ctl00_plcMain_lstGradCollege"))
        college_options = [option.text for option in college_dropdown.options]

        # Iterate through colleges
        for college in college_options:
            try:
                # Refresh college dropdown and select current college
                college_dropdown = Select(driver.find_element(By.ID, "ctl00_plcMain_lstGradCollege"))
                college_dropdown.select_by_visible_text(college)

                # Scroll to the button
                button = driver.find_element(By.ID, "ctl00_plcMain_btnGrade")
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(1)  # Allow page to settle
                button.click()

                # Wait for the page to load
                time.sleep(1)

                # Check if "Report Not Available" is displayed
                if "not available" in driver.page_source.lower():
                    print(f"Report not available for {year}, {semester}, {college}")
                    driver.back()  # Go back to the previous page
                    time.sleep(1)  # Allow the page to reload
                    continue

                # Wait for the PDF to download
                time.sleep(2)

            except ElementClickInterceptedException:
                print("ElementClickInterceptedException occurred. Retrying...")
                driver.execute_script("arguments[0].click();", button)  # Use JavaScript to click

            except StaleElementReferenceException:
                print("StaleElementReferenceException occurred. Reloading page.")
                driver.back()  # Go back to reload the page
                time.sleep(2)  # Wait for the page to reload
                break  # Break out of the loop to refresh elements

# Close the browser
driver.quit()

print(f"PDFs downloaded to {download_dir}")
