#!/usr/bin/env python3
# test_fcm_notification.py
# FCM 알림 테스트 스크립트

import json
import os
import firebase_admin
from firebase_admin import credentials, messaging

def init_firebase():
    """Firebase Admin SDK 초기화"""
    try:
        service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if not service_account_json:
            print("❌ FIREBASE_SERVICE_ACCOUNT 환경변수가 설정되지 않았습니다.")
            return False
        
        cred_dict = json.loads(service_account_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase 초기화 완료")
        return True
    except Exception as e:
        print(f"❌ Firebase 초기화 실패: {e}")
        return False

def send_test_notification():
    """테스트 알림 발송"""
    try:
        topic = os.environ.get('FCM_TOPIC', 'all_users')
        
        message = messaging.Message(
            notification=messaging.Notification(
                title="🎰 테스트 알림",
                body="로또 알림이 정상적으로 작동합니다! 🎉",
            ),
            data={
                'type': 'test',
                'message': 'FCM 알림 테스트',
            },
            topic=topic,
        )
        
        response = messaging.send(message)
        print(f"✅ FCM 알림 발송 완료!")
        print(f"📱 Response: {response}")
        return True
    except Exception as e:
        print(f"❌ FCM 알림 발송 실패: {e}")
        return False

def main():
    print("🧪 FCM 알림 테스트 시작...\n")
    
    if init_firebase():
        send_test_notification()
    else:
        print("❌ Firebase 초기화 실패로 테스트를 중단합니다.")
    
    print("\n✅ 테스트 완료!")

if __name__ == '__main__':
    main()