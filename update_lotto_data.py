#!/usr/bin/env python3
# update_lotto_data.py
# 동행복권 웹페이지에서 최신 회차를 크롤링하여 JSON 파일을 업데이트하고 FCM 알림을 발송합니다.

import json
import requests
import time
import os
import sys
import re
from datetime import datetime
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, messaging

# 설정
JSON_FILE = 'lotto-history.json'
RESULT_PAGE_URL = 'https://www.dhlottery.co.kr/lt645/result'
API_URL = 'https://m.dhlottery.co.kr/lt645/selectPstLt645Info.do?ltEpsd='

# Firebase 초기화 (선택적)
def init_firebase():
    """Firebase Admin SDK 초기화"""
    try:
        service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if not service_account_json:
            print("⚠️ Firebase 서비스 계정 정보가 없습니다. 알림을 건너뜁니다.")
            return False
        
        cred_dict = json.loads(service_account_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase 초기화 완료")
        return True
    except Exception as e:
        print(f"⚠️ Firebase 초기화 실패: {e}")
        return False

def send_fcm_notification(draw_data):
    """FCM 토픽으로 당첨번호 알림 발송"""
    try:
        topic = os.environ.get('FCM_TOPIC', 'all_users')
        
        # 당첨번호 포맷팅
        numbers = f"{draw_data['tm1WnNo']}, {draw_data['tm2WnNo']}, {draw_data['tm3WnNo']}, {draw_data['tm4WnNo']}, {draw_data['tm5WnNo']}, {draw_data['tm6WnNo']}"
        bonus = draw_data['bnsWnNo']
        
        # 메시지 생성
        message = messaging.Message(
            notification=messaging.Notification(
                title=f"🎰 제 {draw_data['ltEpsd']}회 로또 당첨번호",
                body=f"{numbers} + {bonus}",
            ),
            data={
                'type': 'lotto_result',
                'draw_no': str(draw_data['ltEpsd']),
                'numbers': numbers,
                'bonus': str(bonus),
            },
            topic=topic,
        )
        
        # 발송
        response = messaging.send(message)
        print(f"✅ FCM 알림 발송 완료: {response}")
        return True
    except Exception as e:
        print(f"❌ FCM 알림 발송 실패: {e}")
        return False

def get_latest_draw_number():
    """웹페이지에서 최신 회차 번호를 스크래핑"""
    try:
        print("🌐 동행복권 웹페이지에서 최신 회차 확인 중...")
        
        response = requests.get(RESULT_PAGE_URL, timeout=10)
        response.raise_for_status()
        
        # JavaScript 코드에서 회차 번호 추출
        # $("#d-trigger_txt").text("1207" + '회'); 형태를 찾음
        pattern = r'text\("(\d+)"\s*\+\s*[\'"]회[\'"]\)'
        match = re.search(pattern, response.text)
        
        if match:
            latest_draw = int(match.group(1))
            print(f"✅ 웹페이지 최신 회차: {latest_draw}")
            return latest_draw
        else:
            print("⚠️ 웹페이지에서 회차 번호를 찾을 수 없습니다.")
            return None
    except Exception as e:
        print(f"❌ 웹페이지 스크래핑 실패: {e}")
        return None

def fetch_draw_data(draw_no):
    """특정 회차의 로또 데이터를 API에서 가져옵니다."""
    try:
        response = requests.get(f"{API_URL}{draw_no}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # API 응답 확인
        if not data.get('data') or not data['data'].get('list') or len(data['data']['list']) == 0:
            return None
        
        # 첫 번째 항목 추출
        draw_data = data['data']['list'][0]
        
        # 이미 올바른 형식이므로 그대로 반환
        return draw_data
    except Exception as e:
        print(f"❌ {draw_no}회 조회 실패: {e}")
        return None

def load_existing_data():
    """기존 JSON 파일을 불러옵니다."""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ {JSON_FILE} 파일이 없습니다. 새로 생성합니다.")
        return []
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        return []

def save_data(data):
    """데이터를 JSON 파일로 저장합니다."""
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ {JSON_FILE} 저장 완료")
        return True
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
        return False

def main():
    print("🎰 로또 데이터 업데이트 시작...")
    print(f"⏰ 현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Firebase 초기화 (알림용)
    firebase_initialized = init_firebase()
    
    # 1. 기존 데이터 로드
    existing_data = load_existing_data()
    
    if not existing_data:
        print("❌ 기존 데이터를 불러올 수 없습니다.")
        return
    
    # 2. 현재 최대 회차 확인
    max_draw = max(draw['ltEpsd'] for draw in existing_data)
    print(f"📊 로컬 최대 회차: {max_draw}")
    
    # 3. 웹페이지에서 최신 회차 확인
    latest_draw = get_latest_draw_number()
    
    if not latest_draw:
        print("⚠️ 최신 회차를 확인할 수 없어 연속 확인 방식으로 진행합니다.")
        latest_draw = max_draw + 10  # 최대 10회차까지 확인
    
    print(f"📊 웹페이지 최신 회차: {latest_draw}")
    
    # 4. 새로운 회차 수집
    new_draws = []
    
    for draw_no in range(max_draw + 1, latest_draw + 1):
        print(f"🔍 {draw_no}회 확인 중...")
        draw_data = fetch_draw_data(draw_no)
        
        if draw_data:
            print(f"✅ {draw_no}회 발견!")
            new_draws.append(draw_data)
        else:
            print(f"⏭️ {draw_no}회 없음")
        
        time.sleep(1)  # API 호출 간격 (서버 부담 방지)
    
    # 5. 새로운 회차가 있으면 저장 및 알림
    if new_draws:
        print(f"\n🎉 {len(new_draws)}개의 새로운 회차 발견!")
        for draw in new_draws:
            print(f"  - {draw['ltEpsd']}회 ({draw['ltRflYmd']})")
        
        # 기존 데이터에 추가
        existing_data.extend(new_draws)
        
        # 회차순 정렬
        existing_data.sort(key=lambda x: x['ltEpsd'])
        
        # 저장
        if save_data(existing_data):
            print(f"✅ 업데이트 완료! 총 {len(existing_data)}개 회차")
            
            # FCM 알림 발송 (가장 최신 회차만)
            if firebase_initialized:
                latest_draw = new_draws[-1]
                print(f"\n📢 알림 발송 중: {latest_draw['ltEpsd']}회")
                send_fcm_notification(latest_draw)
        else:
            print("❌ 저장 실패")
    else:
        print("\n✅ 이미 최신 상태입니다.")
    
    print("\n🎰 작업 완료!")

if __name__ == '__main__':
    main()