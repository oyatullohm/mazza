# import json
# import requests
# from google.oauth2 import service_account
# from google.auth.transport.requests import Request
# from Admin.settings import FIREBASE_CREDENTIALS
class FCMService:
    pass 
    # SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]
    # FCM_URL ="https://fcm.googleapis.com/v1/projects/egasidan-35edc/messages:send"

    # @classmethod
    # def _get_access_token(cls):
    #     credentials = service_account.Credentials.from_service_account_file(
    #         FIREBASE_CREDENTIALS,  # manzilini moslashtir
    #         scopes=cls.SCOPES
    #     )
    #     credentials.refresh(Request())
    #     return credentials.token

    # @classmethod
    # def send_push_notification(cls, token, title, body, data=None):
    #     access_token = cls._get_access_token()

    #     headers = {
    #         "Authorization": f"Bearer {access_token}",
    #         "Content-Type": "application/json; UTF-8",
    #     }

    #     message = {
    #         "message": {
    #             "token": token,
    #             "notification": {
    #                 "title": title,
    #                 "body": body,
    #             },
    #             "data": data or {},
    #         }
    #     }

    #     response = requests.post(cls.FCM_URL, headers=headers, data=json.dumps(message))
    #     print("🔔 FCM javobi:", response.status_code, response.text)
    #     return response