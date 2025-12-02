import requests

class PushoverClient:
    def __init__(self, user_key: str, app_token: str):
        self.user_key = user_key
        self.app_token = app_token
        self.api_url = "https://api.pushover.net/1/messages.json"

    def send(self, message: str, title: str = None, **kwargs):
        payload = {
            "token": self.app_token,
            "user": self.user_key,
            "message": message,
        }

        if title:
            payload["title"] = title

        payload.update(kwargs)

        try:
            response = requests.post(self.api_url, data=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": 0, "error": str(e)}

    def notify_info(self, message):
        return self.send(message, title="INFO")
