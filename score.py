from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import pymysql

# ✅ 프록시 주소 설정
proxy = "212.110.188.189:34405"

# ✅ 크롬드라이버 설정 - 프록시 및 탐지 방지
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
options.add_argument(f"--proxy-server=http://{proxy}")

service = Service("C:/Users/BIT/Desktop/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

# ✅ Selenium 탐지 방지
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    """
})


# ✅ DB 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    database='compick_project_db',
    charset='utf8mb4'
)
cursor = conn.cursor()

# ✅ 특정 연도 경기만 조회 (예: 2019년)
target_year = "2025"
cursor.execute("""
    SELECT id, home_team_id, away_team_id 
    FROM matches 
    WHERE start_time LIKE %s 
    ORDER BY start_time ASC
""", (f"{target_year}%",))
matches = cursor.fetchall()

# ✅ INSERT SQL - 복합키 (match_id, team_id) 기반 갱신
insert_sql = """
INSERT INTO match_score (match_id, team_id, score)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE
    score = VALUES(score)
"""

saved_count = 0

for match_id, home_id, away_id in matches:
    try:
        url = f"https://api.sofascore.com/api/v1/event/{match_id}"
        driver.get(url)
        time.sleep(2)  # 약간 여유를 줘야 응답이 올 때도 있음
        body = driver.find_element("tag name", "pre").text
        data = json.loads(body)

        event = data.get("event", {})
        home_score = event.get("homeScore", {}).get("current")
        away_score = event.get("awayScore", {}).get("current")

        if home_score is not None and away_score is not None:
            cursor.execute(insert_sql, (match_id, home_id, home_score))
            cursor.execute(insert_sql, (match_id, away_id, away_score))
            saved_count += 2
            print(f"✅ 저장: {match_id} | {home_score}:{away_score}")
        else:
            print(f"❌ 스코어 없음: {match_id}")

    except Exception as e:
        print(f"⚠️ 오류 발생: {match_id} | {e}")

# ✅ 마무리
conn.commit()
cursor.close()
conn.close()
driver.quit()

print(f"🎯 총 저장된 스코어: {saved_count}개")
