from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from driver_caller import Driver  # Ensure this module is correctly implemented
from config.os_config import ROOT_DIR  # Ensure this module is correctly implemented
import os
import csv
import time
from datetime import datetime

# Change to the root directory
os.chdir(ROOT_DIR)

# Initialize the driver using driver_caller
driver = Driver().get_driver()
driver.maximize_window()

# Prepare CSV file for storing results
csv_file_path = os.path.join(ROOT_DIR, 'matches.csv')
csv_file = open(csv_file_path, 'w', newline='', encoding='utf-8')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Tournament', 'Year', 'Date', 'Time', 'Player 1', 'Player 2', 'Score', 'Odds'])

try:
    # Navigate to the main results page
    driver.get("https://www.oddsportal.com/tennis/results/")
    print("Page loaded")

    # Accept cookies if the prompt appears
    try:
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
        )
        accept_button.click()
        print("Accepted cookies")
    except Exception:
        print("No cookie consent button found or already accepted")

    # Wait for the country containers to load
    try:
        country_containers = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'ul.flex.content-start.w-full.text-xs.border-l')
            )
        )
        print("Country containers are loaded")
    except Exception as e:
        print(f"Country containers not found: {e}")
        driver.quit()
        exit()

    print(f"Found {len(country_containers)} country containers")

    # Collect tournament URLs from the first country only
    tournament_urls = []

    if country_containers:
        for country in country_containers:
            try:
                # Click on the country container to expand tournaments
                driver.execute_script("arguments[0].scrollIntoView(true);", country)
                driver.execute_script("arguments[0].click();", country)
                print("Clicked on the first country container to expand tournaments")

                # Wait for tournaments to be visible
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, 'li.flex.items-center a')
                    )
                )

                # Find all tournament links
                tournaments = country.find_elements(
                    By.CSS_SELECTOR,
                    'li.flex.items-center a'
                )
                print(f"Found {len(tournaments)} tournaments in the country")

                for tournament in tournaments:
                    tournament_url = tournament.get_attribute('href')
                    # Ensure the URL ends with '/results/'
                    if not tournament_url.endswith('results/'):
                        tournament_url = tournament_url.rstrip('/') + '/results/'
                    tournament_urls.append(tournament_url)

                # Collapse the country container
                driver.execute_script("arguments[0].click();", country)
                print("Collapsed the country container")
            except Exception as e:
                print(f"Error collecting tournaments: {e}")

            # Now, process all tournaments from the first country
            for tournament_url in tournament_urls:
                try:
                    print(f"Opening tournament: {tournament_url}")
                    driver.get(tournament_url)

                    # Allow the page to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.XPATH, '//h1')
                        )
                    )
                    time.sleep(0.2)  # Additional wait to ensure all elements load

                    # Collect all available years for the tournament
                    try:
                        years_container = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located(
                                (By.XPATH, '//div[contains(@class, "no-scrollbar")]')
                            )
                        )
                        year_links = years_container.find_elements(By.TAG_NAME, 'a')

                        # Collect year URLs and ensure they end with '/results/'
                        year_urls = []
                        for year_link in year_links:
                            year_url = year_link.get_attribute('href')
                            if not year_url.endswith('results/'):
                                year_url = year_url.rstrip('/') + '/results/'
                            year_urls.append(year_url)

                        print(f"Found {len(year_urls)} years for this tournament")
                    except Exception as e:
                        print(f"No years navigation found for this tournament: {e}")
                        year_urls = [tournament_url]  # Default to the current tournament page

                    # Iterate over each year's URL
                    for year_url in year_urls:
                        try:
                            print(f"Processing year URL: {year_url}")
                            driver.get(year_url)

                            # Allow the page to load
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located(
                                    (By.XPATH, '//div[contains(@class, "flex flex-col px-3 text-sm")]')
                                )
                            )
                            time.sleep(0.1)  # Additional wait to ensure all elements load

                            # Find the matches container
                            try:
                                matches_container = driver.find_element(
                                    By.XPATH,
                                    '//div[contains(@class, "flex flex-col px-3 text-sm")]'
                                )
                                print("Matches container loaded")
                            except Exception as e:
                                print(f"Matches container not found: {e}")
                                continue

                            # Find all eventRow divs within the matches container
                            event_rows = matches_container.find_elements(
                                By.XPATH,
                                './/div[contains(@class, "eventRow")]'
                            )
                            print(f"Found {len(event_rows)} total event rows in matches container")

                            # Extract tournament name
                            try:
                                tournament_name = driver.find_element(By.XPATH, '//h1').text.strip()
                            except Exception:
                                tournament_name = 'N/A'

                            # Initialize current_date to 'N/A'
                            current_date = 'N/A'

                            for event_row in event_rows:
                                # Check if the event_row contains a date
                                try:
                                    date_element = event_row.find_element(
                                        By.XPATH,
                                        './/div[contains(@class, "text-black-main") and contains(@class, "font-main")]'
                                    )
                                    match_date_str = date_element.text.strip()
                                    # Parse the date string and format it as YYYYMMDD
                                    match_date = datetime.strptime(match_date_str, '%d %b %Y').strftime('%Y%m%d')
                                    current_date = match_date  # Update current_date
                                except Exception:
                                    match_date = current_date  # Use the last known date

                                # Extract Match Time
                                try:
                                    # The match time is within a <p> tag inside the 'flex w-full' div
                                    time_element = event_row.find_element(
                                        By.XPATH,
                                        './/div[contains(@class, "flex w-full")]//p'
                                    )
                                    match_time = time_element.text.strip()
                                except Exception:
                                    match_time = 'N/A'

                                # Extract Player 1 Name
                                try:
                                    # Player 1 is the first <p> with class 'participant-name' within the first <a> tag
                                    player1_element = event_row.find_element(
                                        By.XPATH,
                                        './/a[contains(@title, "")][1]//p[contains(@class, "participant-name")]'
                                    )
                                    player1 = player1_element.text.strip()
                                except Exception:
                                    player1 = 'N/A'

                                # Extract Player 2 Name
                                try:
                                    # Player 2 is the first <p> with class 'participant-name' within the second <a> tag
                                    player2_element = event_row.find_element(
                                        By.XPATH,
                                        './/a[contains(@title, "")][2]//p[contains(@class, "participant-name")]'
                                    )
                                    player2 = player2_element.text.strip()
                                except Exception:
                                    player2 = 'N/A'

                                # Extract Scores
                                try:
                                    score_elements = event_row.find_elements(
                                        By.XPATH,
                                        './/div[contains(@class, "flex gap-1 font-bold")]//div[contains(@class, "hidden") or contains(@class, "font-bold")]'
                                    )
                                    scores = [elem.text.strip() for elem in score_elements if elem.text.strip()]
                                    score = ' '.join(scores) if scores else 'N/A'
                                except Exception:
                                    score = 'N/A'

                                # Extract Odds
                                try:
                                    odds_elements = event_row.find_elements(
                                        By.XPATH,
                                        './/div[@data-testid="add-to-coupon-button"]//p'
                                    )
                                    if len(odds_elements) >= 2:
                                        odds1 = odds_elements[0].text.strip()
                                        odds2 = odds_elements[1].text.strip()
                                    else:
                                        odds1 = odds2 = 'N/A'
                                except Exception:
                                    odds1 = odds2 = 'N/A'

                                # Extract the Year from the URL
                                year = year_url.rstrip('/').split('-')[-1]
                                if not year.isdigit():
                                    year = 'Current'

                                # Write the extracted match details to CSV
                                csv_writer.writerow([
                                    tournament_name,
                                    year,
                                    match_date,
                                    match_time,
                                    player1,
                                    player2,
                                    score,
                                    f"{odds1}-{odds2}"
                                ])
                                print(
                                    f"Date: {match_date}, Time: {match_time}, Player 1: {player1}, "
                                    f"Player 2: {player2}, Score: {score}, Odds: {odds1}-{odds2}"
                                )

                        except Exception as e:
                            print(f"Error processing year {year_url}: {e}")
                except Exception as e:
                    print(f"Error processing tournament {tournament_url}: {e}")
    else:
        print("No country containers found.")

except Exception as main_e:
    print(f"An unexpected error occurred: {main_e}")

finally:
    # Close the browser and CSV file after scraping is done
    driver.quit()
    csv_file.close()
    print("Browser closed and CSV file saved.")
