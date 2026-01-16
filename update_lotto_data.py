#!/usr/bin/env python3
# update_lotto_data.py
# 동행복권 API에서 최신 회차를 가져와 JSON 파일을 업데이트합니다.

import json
import requests
import time
from datetime import datetime

# 설정
JSON_FILE = 'lotto-history.json'
API_URL = 'https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo='

def fetch_draw_data(draw_no):
    """특정 회차의 로또 데이터를 API에서 가져옵니다."""
    try:
        response = requests.get(f"{API_URL}{draw_no}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # API 응답 확인
        if data.get('returnValue') != 'success':
            return None
            
        # JSON 형식에 맞게 변환
        return {
            'winType0': 0,
            'winType1': 0,
            'winType2': 0,
            'winType3': 0,
            'gmSqNo': 1,
            'ltEpsd': data['drwNo'],
            'tm1WnNo': data['drwtNo1'],
            'tm2WnNo': data['drwtNo2'],
            'tm3WnNo': data['drwtNo3'],
            'tm4WnNo': data['drwtNo4'],
            'tm5WnNo': data['drwtNo5'],
            'tm6WnNo': data['drwtNo6'],
            'bnsWnNo': data['bnusNo'],
            'ltRflYmd': data['drwNoDate'].replace('-', ''),
            'rnk1WnNope': data['firstPrzwnerCo'],
            'rnk1WnAmt': data['firstWinamnt'],
            'rnk1SumWnAmt': data['firstAccumamnt'],
            'rnk2WnNope': 0,
            'rnk2WnAmt': 0,
            'rnk2SumWnAmt': 0,
            'rnk3WnNope': 0,
            'rnk3WnAmt': 0,
            'rnk3SumWnAmt': 0,
            'rnk4WnNope': 0,
            'rnk4WnAmt': 0,
            'rnk4SumWnAmt': 0,
            'rnk5WnNope': 0,
            'rnk5WnAmt': 0,
            'rnk5SumWnAmt': 0,
            'sumWnNope': 0,
            'rlvtEpsdSumNtslAmt': 0,
            'wholEpsdSumNtslAmt': 0,
            'excelRnk': ''
        }
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
    
    # 1. 기존 데이터 로드
    existing_data = load_existing_data()
    
    if not existing_data:
        print("❌ 기존 데이터를 불러올 수 없습니다.")
        return
    
    # 2. 현재 최대 회차 확인
    max_draw = max(draw['ltEpsd'] for draw in existing_data)
    print(f"📊 현재 최대 회차: {max_draw}")
    
    # 3. 다음 회차부터 최신 회차까지 확인
    new_draws = []
    current_draw = max_draw + 1
    consecutive_failures = 0
    
    while consecutive_failures < 3:  # 연속 3회 실패시 중단
        print(f"🔍 {current_draw}회 확인 중...")
        draw_data = fetch_draw_data(current_draw)
        
        if draw_data:
            print(f"✅ {current_draw}회 발견!")
            new_draws.append(draw_data)
            current_draw += 1
            consecutive_failures = 0
        else:
            print(f"⏭️ {current_draw}회 없음")
            consecutive_failures += 1
        
        time.sleep(1)  # API 호출 간격 (서버 부담 방지)
    
    # 4. 새로운 회차가 있으면 저장
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
        else:
            print("❌ 저장 실패")
    else:
        print("\n✅ 이미 최신 상태입니다.")
    
    print("\n🎰 작업 완료!")

if __name__ == '__main__':
    main()