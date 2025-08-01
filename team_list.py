from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import json
import pandas as pd

# ✅ 크롬 드라이버 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
service = Service("C:/Users/BIT/Desktop/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

# ✅ 시즌 및 리그 ID 설정
season_map = {
    "2019/2020": 23776,
    "2020/2021": 29415,
    "2021/2022": 37036,
    "2022/2023": 41886,
    "2023/2024": 52186,
    "2024/2025": 61627
}

league_map = {
    "Premier League": 17,
    "LaLiga": 8,
    "UEFA Champions League": 7
}

all_teams = []

# ✅ 리그 × 시즌 조합 순회
for league_name, tournament_id in league_map.items():
    for season_name, season_id in season_map.items():
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/teams"
        print(f"📡 요청 중: {league_name} - {season_name}")
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
                    "slug": team["slug"],
                    "image_url": f"https://api.sofascore.app/api/v1/team/{team['id']}/image",
                    "league": league_name,
                    "season": season_name
                })

        except Exception as e:
            print(f"❌ 오류 발생: {e}")

driver.quit()

# ✅ team_id 기준 중복 제거
df = pd.DataFrame(all_teams)
unique_df = df.drop_duplicates(subset=["team_id"]).reset_index(drop=True)

# ✅ 저장
unique_df.to_csv("all_unique_teams_2019_2025.csv", index=False, encoding="utf-8-sig")
print(f"✅ 저장 완료: all_unique_teams_2019_2025_0801.csv (총 {len(unique_df)}팀)")
