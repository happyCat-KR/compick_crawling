from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import pymysql
from datetime import datetime

# ✅ 날짜 설정
target_date = "2025-05-25"

# ✅ 크롬 드라이버 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
service = Service("C:/Users/BIT/Desktop/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

# ✅ Sofascore API 호출
url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{target_date}"
driver.get(url)
time.sleep(3)
body = driver.find_element("tag name", "pre").text
data = json.loads(body)
driver.quit()

# ✅ 리그-국가 매핑 정의
league_country_map = {
    "Premier League": "England",
    "LaLiga": "Spain",
    "UEFA Champions League": "Europe"
}
target_leagues = league_country_map.keys()
events = data.get("events", [])

# ✅ DB 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    database='compick_project_db',
    charset='utf8mb4'
)
cursor = conn.cursor()

# ✅ 리그명 → ID 매핑
cursor.execute("SELECT id, league_name FROM league")
league_map = {name: lid for lid, name in cursor.fetchall()}

# ✅ 팀명 → ID 매핑
cursor.execute("SELECT team_id, team_name FROM team_info")
team_map = {name: tid for tid, name in cursor.fetchall()}

# ✅ INSERT SQL
insert_sql = """
INSERT INTO matches (id, league_id, home_team_id, away_team_id, start_time)
VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    league_id = VALUES(league_id),
    home_team_id = VALUES(home_team_id),
    away_team_id = VALUES(away_team_id),
    start_time = VALUES(start_time)
"""

inserted_count = 0
for e in events:
    league_name = e['tournament']['name']
    country_name = e['tournament']['category']['name']

    # ✅ 리그 + 국가 정확히 일치하는 경우만 진행
    if league_name not in target_leagues:
        continue
    if league_country_map[league_name] != country_name:
        continue

    match_id = e['id']
    home_name = e['homeTeam']['name']
    away_name = e['awayTeam']['name']
    start_ts = datetime.fromtimestamp(e['startTimestamp'])

    league_id = league_map.get(league_name)
    home_id = team_map.get(home_name)
    away_id = team_map.get(away_name)

    if not league_id or not home_id or not away_id:
        print(f"❌ 매핑 실패: {league_name} | {home_name} vs {away_name}")
        continue

    cursor.execute(insert_sql, (match_id, league_id, home_id, away_id, start_ts))
    inserted_count += 1

conn.commit()
cursor.close()
conn.close()

print(f"✅ DB 저장 완료: {inserted_count}개 경기")
