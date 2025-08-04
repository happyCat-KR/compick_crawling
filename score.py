from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import pymysql

# ✅ 크롬드라이버 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
service = Service("C:/Users/BIT/Desktop/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

# ✅ DB 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    database='compick_project_db',
    charset='utf8mb4'
)
cursor = conn.cursor()

# ✅ matches 테이블에서 모든 경기 ID 조회
cursor.execute("SELECT id, home_team_id, away_team_id FROM matches")
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
        time.sleep(1.5)
        body = driver.find_element("tag name", "pre").text
        data = json.loads(body)

        event = data.get("event", {})
        home_score = event.get("homeScore", {}).get("current")
        away_score = event.get("awayScore", {}).get("current")

        if home_score is not None and away_score is not None:
            # 홈팀 점수 저장
            cursor.execute(insert_sql, (match_id, home_id, home_score))
            # 어웨이팀 점수 저장
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
