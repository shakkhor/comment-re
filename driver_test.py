from selenium import webdriver

# Set up the WebDriver without specifying the path to ChromeDriver (assuming it's in your PATH)
driver = webdriver.Chrome()

# Test by opening Google
driver.get("https://www.google.com")
print(driver.title)  # Should print "Google"

driver.quit()
