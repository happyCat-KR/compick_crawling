from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import pandas as pd
import pymysql

# ✅ 크롬 드라이버 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
service = Service("C:/Users/BIT/Desktop/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

# ✅ 리그 및 시즌 ID
league_map = {
    "Premier League": 17,
    "LaLiga": 8,
    "UEFA Champions League": 7
}
season_ids = {
    "Premier League": {
        "2025/2026": 76986
    },
    "LaLiga": {
        "2025/2026": 77559
    },
    "UEFA Champions League": {
        "2025/2026": 76953
    }
}

# ✅ 팀 정보 수집
all_teams = []
for league, tid in league_map.items():
    for season, sid in season_ids[league].items():
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{tid}/season/{sid}/teams"
        print(f"📡 {league} {season} 요청 중...")
        try:
            driver.get(url)
            time.sleep(2)
            body = driver.find_element("tag name", "pre").text
            data = json.loads(body)
            teams = data.get("teams", [])
            for team in teams:
                all_teams.append({
                    "team_id": team["id"],
                    "team_name": team["name"],
                    "image_url": f"https://api.sofascore.app/api/v1/team/{team['id']}/image"
                })
        except Exception as e:
            print(f"❌ {league} {season} 오류: {e}")

driver.quit()

# ✅ 중복 제거 및 필요한 컬럼만 추출
df = pd.DataFrame(all_teams)
df_unique = df.drop_duplicates(subset=["team_name"]).reset_index(drop=True)
df_selected = df_unique[['team_id', 'team_name', 'image_url']]

# ✅ DB 저장 (덮어쓰기 방식: UPDATE or INSERT)
inserted_count = 0
updated_count = 0

try:
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='compick_project_db',
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    for _, row in df_selected.iterrows():
        cursor.execute("SELECT 1 FROM team_info WHERE team_id = %s", (row['team_id'],))
        exists = cursor.fetchone()
        if exists:
            cursor.execute("""
                UPDATE team_info
                SET team_name = %s, image_url = %s
                WHERE team_id = %s
            """, (row['team_name'], row['image_url'], row['team_id']))
            updated_count += 1
        else:
            cursor.execute("""
                INSERT INTO team_info (team_id, team_name, image_url)
                VALUES (%s, %s, %s)
            """, (row['team_id'], row['team_name'], row['image_url']))
            inserted_count += 1

    conn.commit()
    print(f"✅ 새로 삽입된 팀 수: {inserted_count}개")
    print(f"🔄 업데이트된 팀 수: {updated_count}개")
except Exception as e:
    print(f"❌ DB 저장 오류: {e}")
finally:
    cursor.close()
    conn.close()
