# Concurrent CLI - Security Load Testing Tool

A lightweight, Python-based CLI tool designed to perform concurrency stress testing on Etsy API endpoints.

Its primary purpose is to validate **Securify** rules (specifically rate-limiting and concurrency blocking) by simulating high-volume simultaneous requests. It uses `asyncio` and `aiohttp` to ensure requests are dispatched in parallel, minimizing client-side latency.

## Features

- **True Concurrency:** Uses non-blocking I/O to send requests simultaneously (not sequentially).
- **OAuth 2.0 Support:** Automatic token handling and refreshing using Etsy's Refresh Token flow.
- **Dynamic Data Injection:** Reads from CSV files to dynamically replace URL parameters (e.g., `{shop_id}`) and inject specific tokens per request.
- **Multi-Mode Testing:** Supports **Burst** (single wave) and **Interval** (soak testing) modes.
- **Detailed Reporting:** Generates a CSV report with a breakdown of HTTP status codes (200, 400, 401/403, 429, 500+).

## Project Structure

```text
concurrent-cli/
├── auth/
│   └── setup_auth.py       # Script to generate initial Refresh Token
├── endpoints/              # JSON configuration files for tests
│   └── getShopReceipts.json
├── data/                   # Input CSV files for dynamic data
│   └── shop_tokens.csv
├── lib/                    # Core logic libraries
├── reports/                # Output results
├── main.py                 # Main CLI entry point
├── .env                    # Environment variables (Ignored by Git)
└── requirements.txt        # Python dependencies
```

## Prerequisites

- Python 3.8 or higher.
- `pip` (Python Package Installer).

## Installation

1. **Clone the repository** (or navigate to the project folder):
   ```bash
   cd concurrent-cli

2. Create a Virtual Environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate

3. Install Dependencies:
   ```bash
    pip install -r requirements.txt


## Installation
1. Configuration:
   ```bash
    # .env
    ETSY_API_KEY=your_actual_api_key_here

2. Run the setup script:
   ```bash
    python auth/setup_auth.py

3. A browser window will open. Log in to Etsy and authorize the app
4. Upon success, the script will automatically save `ETSY_ACCESS_TOKEN` and `ETSY_REFRESH_TOKEN` to your `.env` file

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

## Usage
To run a load test, provide the name of the configuration file (without .json extension) located in the `config/` folder.

```bash
    python main.py --endpoint getShopReceipts
```

## Reporting
Results are logged to the console and saved to data/load_test_results.csv
### CSV Columns:
- Timestamp: Date and time of the batch execution.
- Scenario: Name of the test scenario.
- BatchID: Unique UUID for tracing logs in Securify/Grafana.
- Time(s): Total time taken to execute the batch.
- 200 (OK): Successful requests.
- 400 (Bad Req): Client errors.
- 401/403 (Auth/Block): Requests blocked by Securify or Auth failures.
- 429 (Rate Limit): Requests blocked by Rate Limiting rules.
- 500+ (Errors): Server errors or connectivity issues.