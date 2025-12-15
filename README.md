# Concurrent CLI - Security Load Testing Tool

A lightweight, Python-based CLI tool designed to perform concurrency stress testing on API endpoints.

Its primary purpose is to validate **Securify** rules (specifically rate-limiting and concurrency blocking) by simulating high-volume simultaneous requests. It uses `asyncio` and `aiohttp` to ensure requests are dispatched in parallel, minimizing client-side latency.

## Features

- **True Concurrency:** Uses non-blocking I/O to send requests simultaneously (not sequentially).
- **Reporting:** outputs execution time and a breakdown of HTTP status codes (Success vs. Blocked).

## Prerequisites

- Python 3.8 or higher.
- `pip` (Python Package Installer).

## Installation

1. **Clone the repository** (or navigate to the project folder):
   ```bash
   cd concurrent-cli
   pip install -r requirements.txt

2. Create a Virtual Environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate

3. Configuration:
   ```bash
    # .env
    ETSY_API_KEY=your_actual_api_key_here

4. Usage:
   ```bash
    python main.py

## Modes

### Interval Mode (Recommended for Soak Testing)

Sends a batch of requests periodically for a set duration.

    - `mode`: "interval" (Repeats batches).

    - `duration_minutes`: Total runtime of the test (e.g., 60 minutes).

    - `interval_seconds`: Pause time between batches (e.g., 120 seconds).

    Example: 
    ```bash
    {
        "mode": "interval",
        "duration_minutes": 60,
        "interval_seconds": 120,
        "target_url": "[https://openapi.etsy.com/v3/application/listings/active?limit=100](https://openapi.etsy.com/v3/application/listings/active?limit=100)",
        "method": "GET",
        "concurrency": 100,
        "payload": {},
        "headers": {
            "Content-Type": "application/json"
        }
    }
    ```

### Burst Mode

Sends all the specified concurrency amount of request at the same time.

    - `mode`: "burst".

    Example: 
    ```bash
    {
    "mode": "burst",
    "target_url": "[https://openapi.etsy.com/v3/application/listings/active?limit=100](https://openapi.etsy.com/v3/application/listings/active?limit=100)",
        "method": "GET",
        "concurrency": 100,
        "payload": {},
        "headers": {
            "Content-Type": "application/json"
        }
    }
    ```