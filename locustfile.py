import os
import sys
import logging
import asyncio
import random  # <--- NEW
from locust import FastHttpUser, task, events, constant
from dotenv import load_dotenv

sys.path.append(os.getcwd())

from lib.auth import AuthManager
from lib.files import load_endpoint_config
from lib.constants import ENDPOINTS_DIR

load_dotenv()

# --- GLOBAL SHARED STATE ---
TEST_CONFIGS = []
AUTH_HEADERS = {}

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global TEST_CONFIGS, AUTH_HEADERS
    
    endpoint_name = os.getenv("TARGET_ENDPOINT")
    if not endpoint_name:
        logging.error("❌ STOPPING: 'TARGET_ENDPOINT' env var is missing.")
        environment.runner.quit()
        return

    logging.info(f"📂 Loading config for endpoint: {endpoint_name}")
    configs, error = load_endpoint_config(endpoint_name, ENDPOINTS_DIR)
    
    if error or not configs:
        logging.error(f"❌ Configuration Error: {error}")
        environment.runner.quit()
        return

    # SAVE ALL SCENARIOS
    TEST_CONFIGS = configs 
    logging.info(f"✅ Loaded {len(TEST_CONFIGS)} scenarios.")
    
    # Auth setup (remains the same)
    api_key = os.getenv("ETSY_API_KEY")
    refresh_token = os.getenv("ETSY_REFRESH_TOKEN")
    
    if not api_key or not refresh_token:
        logging.error("❌ Missing .env credentials.")
        environment.runner.quit()
        return

    logging.info("🔐 Refreshing OAuth Token...")
    auth = AuthManager(api_key, refresh_token)
    
    try:
        if hasattr(auth, 'refresh_access_token_sync'):
             success = auth.refresh_access_token_sync()
        else:
             success = asyncio.run(auth.refresh_access_token())
    except Exception as e:
        logging.error(f"❌ Auth Exception: {e}")
        environment.runner.quit()
        return
    
    if not success:
        logging.error("❌ Auth Failed.")
        environment.runner.quit()
        return
        
    AUTH_HEADERS = auth.get_headers()
    logging.info("✅ Ready to swarm!")


class EtsyUser(FastHttpUser):
    network_timeout = 5.0
    connection_timeout = 5.0

    def wait_time(self):
        """
        Calculates wait time. 
        If there are multiple scenarios, uses the interval of the first one as base reference,
        or you could choose one randomly if they vary significantly.
        """
        if TEST_CONFIGS:
            # We take a reference scenario (or you could do random.choice(TEST_CONFIGS))
            ref_config = TEST_CONFIGS[0]
            mode = ref_config.get("mode", "burst")
            interval = ref_config.get("interval_seconds", 1)
            
            if mode == "interval":
                return constant(interval)(self)
            else:
                return constant(0.1)(self)
        return constant(1)(self)

    @task
    def attack_endpoint(self):
        if not TEST_CONFIGS: return

        # --- RANDOM SCENARIO SELECTION ---
        # Every time it fires, picks one from the list (Load Balancing)
        scenario = random.choice(TEST_CONFIGS)

        target_url = scenario['target_url']
        method = scenario['method']
        payload = scenario.get('payload', {})
        
        headers = AUTH_HEADERS.copy()
        if 'headers' in scenario:
            headers.update(scenario['headers'])
        
        # Unique name for grouping in Locust (including scenario name if exists)
        name_prefix = f"[{scenario.get('name', 'Unamed')}]"
        request_name = f"{name_prefix} {method} {target_url}"

        with self.client.request(
            method, 
            target_url, 
            json=payload, 
            headers=headers, 
            name=request_name,
            catch_response=True
        ) as response:
            if response.status_code in [403, 429]:
                response.failure(f"Blocked ({response.status_code})")
            elif response.status_code >= 500:
                response.failure(f"Server Error ({response.status_code})")
            elif response.status_code == 0:
                response.failure("Timeout")