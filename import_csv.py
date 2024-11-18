import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Set up WebDriver with ChromeDriver in PATH
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Optional: Run in headless mode
options.add_argument("--log-level=3")  # Suppress logging

# Initialize the WebDriver
driver = webdriver.Chrome(options=options)

try:
    # Open the YouTube video
    video_url = "https://www.youtube.com/watch?v=ciRnJTOP5Gs"  # Replace with your video URL
    driver.get(video_url)
    time.sleep(5)  # Allow page to load

    # Check if chat replay is available
    try:
        chat_frame = driver.find_element(By.CSS_SELECTOR, "iframe#chatframe")
        driver.switch_to.frame(chat_frame)
        print("Chat frame loaded.")
    except Exception:
        print("Live chat replay is not available for this video.")
        driver.quit()
        exit()

    # Prepare CSV file
    csv_file = "chat_replies.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["Commenter", "Time", "Comment"])

        # Scrape messages
        for _ in range(20):  # Scroll multiple times to load more messages
            time.sleep(2)  # Allow chat to load
            chat_items = driver.find_elements(By.CSS_SELECTOR, "yt-live-chat-text-message-renderer")
            
            for item in chat_items:
                try:
                    commenter = item.find_element(By.CSS_SELECTOR, "#author-name").text
                    timestamp = item.find_element(By.CSS_SELECTOR, ".timestamp").text
                    comment = item.find_element(By.CSS_SELECTOR, "#message").text
                    writer.writerow([commenter, timestamp, comment])
                except Exception:
                    continue
            
            # Scroll down to load more messages
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)

    print(f"Chat messages saved to {csv_file}")

finally:
    driver.quit()
