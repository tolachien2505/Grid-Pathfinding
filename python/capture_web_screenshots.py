import os
import time

output_dir = r"d:\CNTT\TRITUENHANTAO\BTL\IMG"
os.makedirs(output_dir, exist_ok=True)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("[ERROR] Playwright is not installed. Please run: pip install playwright && playwright install chromium")
    exit(1)

def run():
    with sync_playwright() as p:
        print("Launching headless Chromium browser...")
        browser = p.chromium.launch(headless=True)
        # Create standard Full HD context
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        url = "http://localhost:5173/"
        print(f"Navigating to {url}...")
        try:
            page.goto(url, timeout=10000)
        except Exception as e:
            print(f"[ERROR] Can not connect to local server {url}. Make sure React dev server is running on npm run dev.")
            browser.close()
            exit(1)
            
        page.wait_for_selector("canvas")
        time.sleep(2.0) # Wait for page initial load and rendering
        
        # 1. Capture web_map_custom_32.png (Default custom map)
        print("1. Capturing: web_map_custom_32.png...")
        page.screenshot(path=os.path.join(output_dir, "web_map_custom_32.png"))
        
        # 2. Capture web_a_star_animation.png (Cyan search waves)
        print("2. Starting A* search animation...")
        page.click("button:has-text('Chạy giả lập A*')")
        time.sleep(0.8) # Capture wavefront mid-animation
        print("Capturing: web_a_star_animation.png...")
        page.screenshot(path=os.path.join(output_dir, "web_a_star_animation.png"))
        
        # Reload to restore static path
        print("Reloading page to reset simulation...")
        page.reload()
        page.wait_for_selector("canvas")
        time.sleep(1.5)
        
        # 3. Capture web_heuristics_comparison.png (Heuristics chart)
        print("3. Executing Heuristic Comparison...")
        page.click("button:has-text('So sánh Heuristic')")
        time.sleep(1.5)
        # Scroll down to make comparison table and bars fully visible
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        time.sleep(0.5)
        print("Capturing: web_heuristics_comparison.png...")
        page.screenshot(path=os.path.join(output_dir, "web_heuristics_comparison.png"))
        
        # Scroll back up to the top
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.5)
        
        # 4. Capture web_traffic_night_free.png (Set hour to 00:00 - Night)
        print("4. Updating traffic hour to 00:00 (Off-peak)...")
        slider = page.locator("input[type='range']")
        slider.evaluate("(el) => { el.value = '0'; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }")
        time.sleep(1.5)
        print("Capturing: web_traffic_night_free.png...")
        page.screenshot(path=os.path.join(output_dir, "web_traffic_night_free.png"))
        
        # 5. Capture web_traffic_rush_avoidance.png (Set hour to 08:00 - Morning peak)
        print("5. Updating traffic hour to 08:00 (Morning Rush Hour)...")
        slider.evaluate("(el) => { el.value = '8'; el.dispatchEvent(new Event('input', { bubbles: true })); el.dispatchEvent(new Event('change', { bubbles: true })); }")
        time.sleep(1.5)
        print("Capturing: web_traffic_rush_avoidance.png...")
        page.screenshot(path=os.path.join(output_dir, "web_traffic_rush_avoidance.png"))
        
        # 6. Capture web_map_berlin_256.png (Berlin AI map)
        print("6. Loading Berlin (256x256) - Moving AI...")
        select = page.locator("select").first
        select.select_option(label="Berlin (256x256) - Moving AI")
        time.sleep(3.5) # Wait for map fetch and parse
        # Click solve button since Auto-solve is off on large maps
        page.click("button:has-text('Giải tuyến tối ưu')")
        time.sleep(2.0)
        print("Capturing: web_map_berlin_256.png...")
        page.screenshot(path=os.path.join(output_dir, "web_map_berlin_256.png"))
        
        # 7. Capture web_map_boston_256.png (Boston AI map)
        print("7. Loading Boston (256x256) - Moving AI...")
        select.select_option(label="Boston (256x256) - Moving AI")
        time.sleep(3.5) # Wait for map fetch and parse
        page.click("button:has-text('Giải tuyến tối ưu')")
        time.sleep(2.0)
        print("Capturing: web_map_boston_256.png...")
        page.screenshot(path=os.path.join(output_dir, "web_map_boston_256.png"))
        
        browser.close()
        print("SUCCESS: All 7 web screenshots captured and saved to BTL\\IMG.")

if __name__ == "__main__":
    run()
