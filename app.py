from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import requests
import math
import time
import os

app = Flask(__name__)

# 봇 토큰 & 채팅 ID
TOKEN = '8047332194:AAHGDD1IRnJh-rvasMxLSt7SfMLJMmPCiqc'
CHAT_ID = 'me'  # 실제 chat_id 숫자 ID 권장

# 텔레그램 전송 함수
def send_telegram_message(text):
    print(f"[텔레그램] 전송됨: {text}")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': text}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[텔레그램] 전송 실패: {e}")

# 베픽 실시간 결과 크롤링
def fetch_powerball_results():
    print("[분석기] 베픽 데이터 수집 시작")
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(executable_path="./chromedriver")  # 현재 폴더의 chromedriver
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://bepick.net/#/game/default/dhrpowerball")
    time.sleep(3)
    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    elements = soup.select("div.noflf")
    numbers = [int(el.text.strip()) for el in elements if el.text.strip().isdigit()]
    print(f"[분석기] 수집된 결과: {numbers[:15]}")
    return numbers[:15]

# 분석 및 EV 계산
def analyze(data):
    print("[분석기] 계산 시작")
    if len(data) < 5:
        return

    freq = {i: data.count(i) / len(data) for i in range(10)}
    appearance = {}
    running_count = 0

    for n in data:
        appearance[n] = appearance.get(n, 0) + 1
        base = +1 if n <= 4 else -1
        count = appearance[n]
        weight = 1.0 if count == 1 else 0.7 if count == 2 else 1.0 if count == 3 else 1.3 if count == 4 else 1.5
        adjust = 1 - (freq[n] - 0.1)
        running_count += base * weight * adjust

    true_count = running_count / math.sqrt(max(1, len(data)))
    win_under = 0.5 + true_count * 0.02
    win_over = 1 - win_under
    ev_under = win_under * 1.95 - (1 - win_under)
    ev_over = win_over * 1.95 - (1 - win_over)

    pick = "보류"
    if win_under >= 0.515 and ev_under > ev_over + 0.03:
        pick = f"언더 ({(win_under*100):.1f}%)"
    elif win_over >= 0.515 and ev_over > ev_under + 0.03:
        pick = f"오버 ({(win_over*100):.1f}%)"

    msg = f"[SoftBayes 자동 픽]\n예상 언더 승률: {(win_under*100):.1f}%\nEV 언더: {ev_under:.3f}\nEV 오버: {ev_over:.3f}\n추천 픽: {pick}"
    send_telegram_message(msg)

@app.route('/')
def run():
    try:
        data = fetch_powerball_results()
        analyze(data)
        return "OK"
    except Exception as e:
        print(f"[오류] {e}")
        return "ERR"
