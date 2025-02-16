from locust import HttpUser, task, between
from random import randint, choice
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MerchantShopUser(HttpUser):
    wait_time = between(0.01, 0.1)
    token = None
    username = None
    
    def on_start(self):
        try:
            self.username = f"loadtest_user_{randint(1, 100000)}"
            
            with self.client.post(
                "/api/auth",
                json={
                    "username": self.username,
                    "password": "testpass123"
                },
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    self.token = response.json()["token"]
                    self.client.headers = {"Authorization": f"Bearer {self.token}"}
                    response.success()
                elif response.status_code == 429:
                    time.sleep(1)
                    self.on_start()
                else:
                    response.failure(f"Auth failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Auth error: {str(e)}")
            time.sleep(1)
            self.on_start()
    
    @task(5)
    def check_info(self):
        with self.client.get("/api/info", catch_response=True) as response:
            if response.status_code == 429:
                response.success()
            elif response.status_code != 200:
                response.failure(f"Info failed: {response.status_code}")
    
    @task(2)
    def buy_item(self):
        items = ["t-shirt", "cup", "book", "pen", "powerbank", 
                "hoody", "umbrella", "socks", "wallet", "pink-hoody"]
        item = choice(items)
        
        with self.client.get(f"/api/buy/{item}", catch_response=True) as response:
            if response.status_code == 429:
                response.success()
            elif response.status_code != 200:
                response.failure(f"Purchase failed: {response.status_code}")
    
    @task(1)
    def send_coins(self):
        if not hasattr(self, 'last_send_time'):
            self.last_send_time = 0
        
        current_time = time.time()
        if current_time - self.last_send_time < 1:
            return
        
        amount = randint(1, 50)
        recipient = f"loadtest_user_{randint(1, 100000)}"
        
        with self.client.post(
            "/api/sendCoin",
            json={"toUser": recipient, "amount": amount},
            catch_response=True
        ) as response:
            if response.status_code == 429:
                response.success()
            elif response.status_code != 200:
                response.failure(f"Send coins failed: {response.status_code}")
            
            self.last_send_time = current_time
