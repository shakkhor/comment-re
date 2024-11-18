import csv
import time
import datetime
import logging
from dataclasses import dataclass
from typing import List, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# Data structure for chat messages
@dataclass
class ChatMessage:
    video_time: str
    author: str
    timestamp: str
    message: str
    
    def to_csv_row(self) -> List[str]:
        return [self.video_time, self.author, self.timestamp, self.message]
    
    def get_unique_id(self) -> str:
        return f"{self.author}_{self.timestamp}_{self.message}"

class YouTubeChatScraper:
    BATCH_SIZE = 500
    
    def __init__(self, video_url: str, output_file: str):
        self.video_url = video_url
        self.output_file = output_file
        self.seen_messages: Set[str] = set()
        self.current_batch: List[ChatMessage] = []
        self.total_messages = 0
        self.setup_logging()
        self.setup_driver()
        
    def setup_logging(self):
        """Configure logging settings"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('youtube_chat_scraper.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """Initialize the Chrome WebDriver with appropriate options"""
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3")
        options.add_argument("--mute-audio")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 20)
        
    def format_duration(self, seconds: int) -> str:
        """Convert seconds to HH:MM:SS format"""
        return str(datetime.timedelta(seconds=seconds))
    
    def write_batch_to_csv(self) -> None:
        """Write the current batch of messages to CSV file"""
        mode = 'a' if self.total_messages > self.BATCH_SIZE else 'w'
        
        try:
            with open(self.output_file, mode=mode, newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                if mode == 'w':  # Write header only for new file
                    writer.writerow(["Video Time", "Commenter", "Time", "Comment"])
                
                for message in self.current_batch:
                    writer.writerow(message.to_csv_row())
            
            self.logger.info(f"Successfully wrote batch of {len(self.current_batch)} messages to CSV")
            self.current_batch.clear()
            
        except Exception as e:
            self.logger.error(f"Error writing to CSV: {e}")
            raise
    
    def get_video_duration(self) -> int:
        """Get video duration in seconds"""
        try:
            duration_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.ytp-time-duration"))
            )
            duration_parts = duration_element.text.split(':')
            
            if len(duration_parts) == 2:  # MM:SS
                return int(duration_parts[0]) * 60 + int(duration_parts[1])
            else:  # HH:MM:SS
                return int(duration_parts[0]) * 3600 + int(duration_parts[1]) * 60 + int(duration_parts[2])
                
        except Exception as e:
            self.logger.warning(f"Could not get video duration: {e}")
            return 14400  # Default to 4 hours
    
    def start_video_playback(self) -> None:
        """Start video playback"""
        try:
            play_button = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "button.ytp-play-button"))
            )
            play_button.click()
            self.logger.info("Started video playback")
            
        except Exception as e:
            self.logger.error(f"Could not start playback: {e}")
            raise
    
    def switch_to_chat_frame(self) -> None:
        """Switch to the chat iframe"""
        try:
            chat_frame = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#chatframe"))
            )
            self.driver.switch_to.frame(chat_frame)
            self.logger.info("Successfully switched to chat frame")
            
        except TimeoutException:
            self.logger.error("Chat frame not found")
            raise
    
    def process_chat_message(self, item, video_time: str) -> None:
        """Process a single chat message element"""
        try:
            message = ChatMessage(
                video_time=video_time,
                author=item.find_element(By.CSS_SELECTOR, "#author-name").text,
                timestamp=item.find_element(By.CSS_SELECTOR, "#timestamp").text,
                message=item.find_element(By.CSS_SELECTOR, "#message").text
            )
            
            message_id = message.get_unique_id()
            if message_id not in self.seen_messages:
                self.seen_messages.add(message_id)
                self.current_batch.append(message)
                self.total_messages += 1
                
                # Print to console
                print(f"\n[{message.video_time}] {message.author} ({message.timestamp}): {message.message}")
                
                # Check if batch is full
                if len(self.current_batch) >= self.BATCH_SIZE:
                    self.logger.info(f"Batch full ({self.BATCH_SIZE} messages). Writing to file...")
                    self.write_batch_to_csv()
                    
        except (NoSuchElementException, StaleElementReferenceException):
            pass
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def scrape(self) -> None:
        """Main scraping method"""
        try:
            self.logger.info(f"Starting scrape of video: {self.video_url}")
            self.driver.get(self.video_url)
            time.sleep(5)
            
            duration_seconds = self.get_video_duration()
            self.logger.info(f"Video duration: {self.format_duration(duration_seconds)}")
            
            self.start_video_playback()
            self.switch_to_chat_frame()
            
            start_time = time.time()
            
            while True:
                current_time = time.time() - start_time
                if current_time >= duration_seconds:
                    self.logger.info("Reached end of video")
                    break
                
                try:
                    # Switch to main frame for video time
                    self.driver.switch_to.default_content()
                    current_time_element = self.driver.find_element(
                        By.CSS_SELECTOR, "span.ytp-time-current"
                    )
                    video_time = current_time_element.text
                    
                    # Switch back to chat frame
                    self.switch_to_chat_frame()
                    
                    # Get chat messages
                    items = self.driver.find_elements(
                        By.CSS_SELECTOR, "yt-live-chat-text-message-renderer"
                    )
                    
                    for item in items:
                        self.process_chat_message(item, video_time)
                    
                    # Print progress every 30 seconds
                    if int(current_time) % 30 == 0:
                        self.logger.info(
                            f"Progress: {self.format_duration(int(current_time))} / "
                            f"{self.format_duration(duration_seconds)}"
                        )
                        self.logger.info(f"Total messages collected: {self.total_messages}")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"Error during iteration: {e}")
                    self.switch_to_chat_frame()
                    continue
            
            # Write any remaining messages
            if self.current_batch:
                self.write_batch_to_csv()
            
            self.logger.info(f"Scraping completed. Total messages collected: {self.total_messages}")
            
        except Exception as e:
            self.logger.error(f"Fatal error during scraping: {e}")
            raise
            
        finally:
            self.driver.quit()

def main():
    VIDEO_URL = "https://www.youtube.com/watch?v=ciRnJTOP5Gs"  # Replace with your video URL
    OUTPUT_FILE = "output.csv"
    
    scraper = YouTubeChatScraper(VIDEO_URL, OUTPUT_FILE)
    scraper.scrape()

if __name__ == "__main__":
    main()