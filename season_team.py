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
        "2019/2020": 23776,
        "2020/2021": 29415,
        "2021/2022": 37036,
        "2022/2023": 41886,
        "2023/2024": 52186,
        "2024/2025": 61627
    },
    "LaLiga": {
        "2019/2020": 24127,
        "2020/2021": 32501,
        "2021/2022": 37223,
        "2022/2023": 42409,
        "2023/2024": 52376,
        "2024/2025": 61643
    },
    "UEFA Champions League": {
        "2019/2020": 23766,
        "2020/2021": 29267,
        "2021/2022": 36886,
        "2022/2023": 41897,
        "2023/2024": 52162,
        "2024/2025": 61644
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

# ✅ DB 저장
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
        cursor.execute("""
            INSERT INTO team_info (team_id, team_name, image_url)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                team_name = VALUES(team_name),
                image_url = VALUES(image_url)
        """, (row['team_id'], row['team_name'], row['image_url']))
    conn.commit()
    print(f"✅ DB 저장 완료: {len(df_selected)}개 팀")
except Exception as e:
    print(f"❌ DB 저장 오류: {e}")
finally:
    cursor.close()
    conn.close()
