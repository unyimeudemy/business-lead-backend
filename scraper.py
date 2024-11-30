from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re

# Set up Chrome WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
service = Service(ChromeDriverManager().install())

driver = webdriver.Chrome(service=service, options=chrome_options)

def scrap(keyword):

    try:
        #keyword = "lawyer"  # Search query
        driver.get(f'https://www.google.com/maps/search/{keyword}/')

        # Accept cookies if prompted
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
        except Exception:
            pass

        # Scroll through the results to load more businesses
        scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        driver.execute_script("""
            var scrollableDiv = arguments[0];
            function scrollWithinElement(scrollableDiv) {
                return new Promise((resolve, reject) => {
                    var totalHeight = 0;
                    var distance = 1000;
                    var scrollDelay = 3000;
                    
                    var timer = setInterval(() => {
                        var scrollHeightBefore = scrollableDiv.scrollHeight;
                        scrollableDiv.scrollBy(0, distance);
                        totalHeight += distance;

                        if (totalHeight >= scrollHeightBefore) {
                            totalHeight = 0;
                            setTimeout(() => {
                                var scrollHeightAfter = scrollableDiv.scrollHeight;
                                if (scrollHeightAfter > scrollHeightBefore) {
                                    return;
                                } else {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, scrollDelay);
                        }
                    }, 200);
                });
            }
            return scrollWithinElement(scrollableDiv);
        """, scrollable_div)

        # Find business elements
        items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')
        results = []

        for item in items:
            data = {}

            try:
                # Business Name
                data['name'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
            except Exception:
                data['name'] = None

            try:
                # Address
                data['address'] = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium').text
            except Exception:
                data['address'] = None

            try:
                # Phone Number
                text_content = item.text
                phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,3}))'
                matches = re.findall(phone_pattern, text_content)
                phone_numbers = [match[0] for match in matches]
                data['phone'] = phone_numbers[0] if phone_numbers else None
            except Exception:
                data['phone'] = None

            try:
                # Hours of Operation
                data['hours'] = item.find_element(By.CSS_SELECTOR, '#QA0Szd > div > div > div.w6VYqd > div.bJzME.Hu9e2e.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde > div:nth-child(7) > div.OqCZI.fontBodyMedium.WVXvdc > div.OMl5r.hH0dDd.jBYmhd > div.MkV9 > div > span.ZDu9vd > span > span:nth-child(2)').text
            except Exception:
                data['hours'] = None

            try:
                # Reviews & Ratings
                rating_text = item.find_element(By.CSS_SELECTOR, '.fontBodyMedium > span[role="img"]').get_attribute('aria-label')
                rating_numbers = [float(piece.replace(",", ".")) for piece in rating_text.split(" ") if piece.replace(",", ".").replace(".", "", 1).isdigit()]
                data['rating'] = rating_numbers[0] if rating_numbers else None
                data['reviews'] = int(rating_numbers[1]) if len(rating_numbers) > 1 else None
            except Exception:
                data['rating'] = None
                data['reviews'] = None

            try:
                # Website Link
                data['website'] = item.find_element(By.CSS_SELECTOR, 'a[data-item-id="website"]').get_attribute('href')
            except Exception:
                data['website'] = None

            if data.get('name'):  # Only include valid entries
                results.append(data)

        # Save results to a JSON file
        #with open('results.json', 'w', encoding='utf-8') as f:
            #json.dump(results, f, ensure_ascii=False, indent=2)

    finally:
        #time.sleep(5)  # Allow some buffer time before quitting
        driver.quit()
    return results

#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div:nth-child(7) > div:nth-child(3) > button > div > div.rogA2c > div.Io6YTe.fontBodyMedium.kR99db.fdkmkc
#QA0Szd > div > div > div.w6VYqd > div.bJzME.Hu9e2e.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde > div:nth-child(7) > div.OqCZI.fontBodyMedium.WVXvdc > div.OMl5r.hH0dDd.jBYmhd > div.MkV9 > div > span.ZDu9vd > span > span:nth-child(2)
#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div:nth-child(7) > div:nth-child(3) > button > div > div.rogA2c
#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div:nth-child(7) > div:nth-child(3) > button > div > div.rogA2c > div.Io6YTe.fontBodyMedium.kR99db.fdkmkc

