from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
from datetime import datetime
import pandas as pd

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

# ✅ 리그-국가 매핑
league_country_map = {
    "Premier League": "England",
    "LaLiga": "Spain",
    "UEFA Champions League": "Europe"
}

# ✅ 대상 리그만 필터
target_leagues = league_country_map.keys()
events = data.get("events", [])

# ✅ CSV 저장용 리스트
csv_rows = []

for e in events:
    league_name = e['tournament']['name']
    country_name = e['tournament']['category']['name']

    # ✅ 리그명이 일치하고, 해당 리그에 대한 정확한 국가명이 일치할 때만 포함
    if league_name not in target_leagues:
        continue
    if league_country_map[league_name] != country_name:
        continue

    match_id = e['id']
    home_name = e['homeTeam']['name']
    away_name = e['awayTeam']['name']
    start_ts = datetime.fromtimestamp(e['startTimestamp'])

    csv_rows.append({
        "match_id": match_id,
        "league_name": league_name,
        "country_name": country_name,
        "home_team": home_name,
        "away_team": away_name,
        "start_time": start_ts
    })

# ✅ pandas로 CSV 저장
df = pd.DataFrame(csv_rows)
df.to_csv(f"matches_{target_date}.csv", index=False, encoding="utf-8-sig")

print(f"✅ CSV 저장 완료: matches_{target_date}.csv ({len(df)}개 경기)")
