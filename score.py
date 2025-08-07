from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import pymysql
from datetime import datetime, timedelta

# ✅ 프록시 주소 설정 (필요 시 수정)
proxy = "38.147.98.190:8080"

# ✅ 크롬드라이버 설정
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

# ✅ 오늘 날짜 기준 ±7일 범위 생성
today = datetime.today()
start_range = (today - timedelta(days=7)).strftime('%Y-%m-%d')
end_range = (today + timedelta(days=7)).strftime('%Y-%m-%d')

# ✅ 범위 내 경기만 조회
cursor.execute("""
    SELECT id, home_team_id, away_team_id 
    FROM matches 
    WHERE start_time BETWEEN %s AND %s
    ORDER BY start_time ASC
""", (start_range, end_range))
matches = cursor.fetchall()

# ✅ INSERT SQL - 점수 저장
insert_score_sql = """
INSERT INTO match_score (match_id, team_id, score)
VALUES (%s, %s, %s)
ON DUPLICATE KEY UPDATE
    score = VALUES(score)
"""

# ✅ UPDATE SQL - 경기 상태 저장
update_match_sql = """
UPDATE matches 
SET status_code = %s
WHERE id = %s
"""

saved_count = 0

for match_id, home_id, away_id in matches:
    try:
        url = f"https://api.sofascore.com/api/v1/event/{match_id}"
        driver.get(url)
        time.sleep(1.5)
        body = driver.find_element("tag name", "pre").text
        data = json.loads(body)

        event = data.get("event", {})

        # ✅ 스코어 추출
        home_score = event.get("homeScore", {}).get("current")
        away_score = event.get("awayScore", {}).get("current")

        if home_score is not None and away_score is not None:
            cursor.execute(insert_score_sql, (match_id, home_id, home_score))
            cursor.execute(insert_score_sql, (match_id, away_id, away_score))
            saved_count += 2
            print(f"✅ 스코어 저장: {match_id} | {home_score}:{away_score}")
        else:
            print(f"❌ 스코어 없음: {match_id}")

        # ✅ 상태 코드 저장
        status_code = event.get("status", {}).get("code")
        if status_code is not None:
            cursor.execute(update_match_sql, (status_code, match_id))
            print(f"📦 상태 저장: {match_id} | status_code={status_code}")

    except Exception as e:
        print(f"⚠️ 오류 발생: {match_id} | {e}")

# ✅ 마무리
conn.commit()
cursor.close()
conn.close()
driver.quit()

print(f"🎯 총 저장된 스코어: {saved_count}개")
