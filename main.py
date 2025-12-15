import asyncio
import aiohttp
import json
import argparse
import time
import uuid
from collections import Counter
import os
from dotenv import load_dotenv

# load env
load_dotenv()

# 1. CLI Setup
parser = argparse.ArgumentParser(description="Testing tool for concurrency")
parser.add_argument("--config", type=str, default="config.json", help="config file route")
args = parser.parse_args()

async def send_request(session, url, method, data, headers, request_id):
    """
    Send 1 request
    """
    try:
        start_time = time.perf_counter()
        async with session.request(method, url, json=data, headers=headers) as response:
            await response.text()
            elapsed = (time.perf_counter() - start_time) * 1000 # ms
            return {
                "id": request_id,
                "status": response.status,
                "latency_ms": elapsed
            }
    except Exception as e:
        return {"id": request_id, "status": "ERROR", "error": str(e)}

async def run_batch(session, config, base_headers, batch_num, scenario_name):
    """
    Executes a SINGLE batch of concurrent requests.
    """
    batch_id = str(uuid.uuid4())
    # Log with Scenario Name prefix
    print(f"\n[{scenario_name}] >>> Starting Batch #{batch_num} | Batch ID: {batch_id}")
    
    current_headers = base_headers.copy()
    current_headers["X-Test-Run-ID"] = batch_id
    
    tasks = []
    for i in range(config['concurrency']):
        task = send_request(
            session, 
            config['target_url'], 
            config['method'], 
            config['payload'], 
            current_headers,
            i + 1
        )
        tasks.append(task)
    
    start_batch = time.perf_counter()
    results = await asyncio.gather(*tasks)
    end_batch = time.perf_counter()
    
    status_counts = Counter(r['status'] for r in results)
    blocked = status_counts.get(429, 0) + status_counts.get(403, 0)
    success = status_counts.get(200, 0)
    errors = status_counts.get(503, 0)
    
    print(f"    [{scenario_name}] Batch #{batch_num} Done | Time: {(end_batch - start_batch):.2f}s | OK: {success} | Blocked: {blocked} | Errors: {errors}")
    return results

async def run_scenario(scenario_config, api_key):
    """
    Handles the logic (Burst/Interval) for a SINGLE scenario config object.
    """
    # Use a default name if not provided
    name = scenario_config.get("name", "Unnamed Scenario")
    
    # Headers Setup
    headers = scenario_config.get("headers", {})
    headers["x-api-key"] = api_key 
    headers["X-Is-Load-Test"] = "true"

    mode = scenario_config.get("mode", "burst")
    duration_minutes = scenario_config.get("duration_minutes", 1)
    interval_seconds = scenario_config.get("interval_seconds", 60)
    concurrency = scenario_config.get("concurrency", 10)

    print(f"--- Init Scenario: '{name}' ---")
    print(f"    Target: {scenario_config['method']} {scenario_config['target_url']}")
    print(f"    Mode: {mode.upper()} | Concurrency: {concurrency}")

    if mode == "interval":
        end_time = time.time() + (duration_minutes * 60)
    else:
        end_time = time.time()

    # Each scenario gets its own session to be independent
    async with aiohttp.ClientSession() as session:
        batch_counter = 1
        
        while True:
            await run_batch(session, scenario_config, headers, batch_counter, name)
            
            if mode == "burst":
                print(f"[{name}] Burst finished.")
                break
            
            if time.time() >= end_time:
                print(f"[{name}] Time limit reached. Stopping.")
                break
            
            # Wait for next interval
            print(f"[{name}] Sleeping {interval_seconds}s...")
            await asyncio.sleep(interval_seconds)
            batch_counter += 1

async def main():
    # 1. Load Config (Now expecting a LIST)
    with open(args.config, 'r') as f:
        config_data = json.load(f)

    # Validate if it's a list or a single object (backward compatibility)
    if isinstance(config_data, dict):
        scenarios = [config_data]
    else:
        scenarios = config_data

    # 2. Get API Key
    api_key = os.getenv("ETSY_API_KEY")
    if not api_key:
        print("ERROR: ETSY_API_KEY not found in .env file")
        return

    # 3. Launch all scenarios in parallel
    print(f"Loaded {len(scenarios)} scenarios. Launching parallel execution...\n")
    
    tasks = []
    for scenario in scenarios:
        # Create a task for each scenario
        tasks.append(run_scenario(scenario, api_key))
    
    # Wait for all scenarios to finish
    await asyncio.gather(*tasks)
    print("\n--- All Scenarios Completed ---")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")