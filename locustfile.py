from locust import HttpUser, task, events
from lib.auth import AuthManager
from lib.config_loader import load_csv_data

auth = AuthManager(API_KEY, REFRESH_TOKEN)

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    auth.refresh_access_token_sync() 

class EtsyUser(HttpUser):
    @task
    def get_receipts(self):
        headers = auth.get_headers()
        self.client.get("/url", headers=headers)