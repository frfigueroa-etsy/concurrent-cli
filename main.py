# main.py

import asyncio
import aiohttp
import argparse
import time
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

# Import our new modules
from lib.auth import AuthManager
from lib.files import init_csv, load_csv_data, append_result_to_csv, load_endpoint_config
from lib.constants import ENDPOINTS_DIR

# Load env variables
load_dotenv()

# CLI Setup
parser = argparse.ArgumentParser(description="Etsy Load Testing Tool")
parser.add_argument(
    "--endpoint", 
    type=str, 
    required=True, 
    help="Name of the endpoint config file inside 'endpoints/' folder"
)
args = parser.parse_args()

async def send_request(session, url, method, data, headers, request_id):
    """Performs the HTTP request and measures latency."""
    try:
        start_time = time.perf_counter()
        async with session.request(method, url, json=data, headers=headers) as response:
            await response.text() # Consume body
            elapsed = (time.perf_counter() - start_time) * 1000
            return {"status": response.status, "latency": elapsed}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

async def run_batch(session, config, auth_manager, batch_num, scenario_name):
    """Executes a single batch of concurrent requests."""
    batch_id = str(uuid.uuid4())
    print(f"\n[{scenario_name}] >>> Batch #{batch_num} | ID: {batch_id}")
    
    # 1. Prepare Headers
    base_headers = auth_manager.get_headers()
    base_headers["X-Test-Run-ID"] = batch_id
    if "headers" in config:
        base_headers.update(config["headers"])

    # 2. Prepare Tasks
    tasks = []
    path_params_file = config.get('pathParams')
    csv_rows = load_csv_data(path_params_file)

    if csv_rows:
        print(f"    Target: {len(csv_rows)} rows x {config['concurrency']} requests")
        req_id = 1
        for row in csv_rows:
            url = config['target_url']
            # Dynamic Replace
            for key, val in row.items():
                url = url.replace(f"{{{key}}}", val)
            
            # Spawn concurrent tasks for this row
            for _ in range(config['concurrency']):
                tasks.append(send_request(session, url, config['method'], config['payload'], base_headers, req_id))
                req_id += 1
    else:
        # Static URL
        url = config['target_url']
        for i in range(config['concurrency']):
            tasks.append(send_request(session, url, config['method'], config['payload'], base_headers, i+1))

    # 3. Execution
    start = time.perf_counter()
    results = await asyncio.gather(*tasks)
    duration = time.perf_counter() - start

    # 4. Process Stats
    stats = {"200": 0, "400": 0, "401_403": 0, "429": 0, "500_other": 0}

    for res in results:
        status = res['status']
        if isinstance(status, str): 
            stats["500_other"] += 1
        elif status == 200:
            stats["200"] += 1
        elif status == 400:
            stats["400"] += 1
        elif status in [401, 403]:
            stats["401_403"] += 1
        elif status == 429:
            stats["429"] += 1
        else:
            stats["500_other"] += 1

    total_reqs = len(results)

    # 5. Output & Reporting
    print(f"    Done in {duration:.2f}s | Total: {total_reqs}")
    print(f"    📊 Stats -> 200: {stats['200']} | 400: {stats['400']} | Auth: {stats['401_403']} | RateLimit: {stats['429']} | Err: {stats['500_other']}")

    append_result_to_csv(
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        scenario_name, batch_num, batch_id, duration, stats, total_reqs
    )

async def run_scenario(scenario, auth_manager):
    """Runs the loop for a specific scenario configuration."""
    name = scenario.get("name", "Unnamed")
    mode = scenario.get("mode", "burst")
    duration = scenario.get("duration_minutes", 1) * 60
    interval = scenario.get("interval_seconds", 60)
    end_time = time.time() + duration

    print(f"--- Init Scenario: {name} ({mode}) ---")

    async with aiohttp.ClientSession() as session:
        batch = 1
        while True:
            await run_batch(session, scenario, auth_manager, batch, name)
            
            if mode == "burst" or time.time() >= end_time:
                print(f"[{name}] Finished.")
                break
            
            print(f"[{name}] Sleeping {interval}s...")
            await asyncio.sleep(interval)
            batch += 1

async def main():
    # 1. Initialize Report
    init_csv()
    
    # 2. Credentials Check
    api_key = os.getenv("ETSY_API_KEY")
    refresh_token = os.getenv("ETSY_REFRESH_TOKEN")

    if not api_key or not refresh_token:
        print("❌ ERROR: Missing ETSY_API_KEY / ETSY_REFRESH_TOKEN in .env")
        return

    # 3. Load Config (Dynamic JSON)
    scenarios, error = load_endpoint_config(args.endpoint, ENDPOINTS_DIR)
    if error:
        print(f"❌ {error}")
        return

    # 4. Authenticate
    auth = AuthManager(api_key, refresh_token)
    if not await auth.refresh_access_token():
        print("❌ Auth Failed. Token expired or invalid.")
        return

    # 5. Launch
    print(f"🚀 Starting {len(scenarios)} scenarios...")
    await asyncio.gather(*[run_scenario(s, auth) for s in scenarios])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest Stopped.")