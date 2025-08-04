from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import pymysql
from datetime import datetime, timedelta

# ✅ 날짜 범위 설정 (19/20 시즌 ~ 24/25 시즌 종료 예상일)
start_date = datetime.strptime("2019-07-01", "%Y-%m-%d")
end_date = datetime.strptime("2025-06-30", "%Y-%m-%d")

# ✅ 크롬 드라이버 설정
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

# ✅ 리그-국가 매핑 정의
league_country_map = {
    "UEFA Champions League": "Europe"
}
target_leagues = league_country_map.keys()

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
current_date = start_date

while current_date <= end_date:
    date_str = current_date.strftime("%Y-%m-%d")
    print(f"📅 처리 중: {date_str}")

    try:
        url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
        driver.get(url)
        time.sleep(1.5)
        body = driver.find_element("tag name", "pre").text
        data = json.loads(body)

        events = data.get("events", [])
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

    except Exception as ex:
        print(f"⚠️ 오류: {date_str} | {ex}")

    current_date += timedelta(days=1)

# ✅ 정리
conn.commit()
cursor.close()
conn.close()
driver.quit()

print(f"✅ 전체 저장 완료: {inserted_count}개 경기")
