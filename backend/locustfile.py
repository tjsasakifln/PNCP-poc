"""
Locust load testing for BidIQ Backend API.

Tests:
- Search endpoint performance under concurrent load
- Download endpoint throughput
- Health check latency

Run locally:
    locust -f locustfile.py --host=http://localhost:8000

Run headless:
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 50 --spawn-rate 5 --run-time 60s --headless

Run in CI:
    locust -f locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 120s \
           --headless --only-summary --csv=results/load-test
"""

import random
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


# ============================================================================
# Test Data Generators
# ============================================================================

UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]

SETORES = ["UNIFORMES", "ALIMENTACAO", "TI", "SAUDE", "EDUCACAO"]


def get_random_ufs(min_count=1, max_count=5):
    """Get random selection of UFs."""
    count = random.randint(min_count, max_count)
    return random.sample(UFS, count)


def get_date_range(days_back=7):
    """Get date range for search (last N days)."""
    hoje = datetime.now()
    data_final = hoje.strftime("%Y-%m-%d")
    data_inicial = (hoje - timedelta(days=days_back)).strftime("%Y-%m-%d")
    return data_inicial, data_final


def get_random_setor():
    """Get random sector."""
    return random.choice(SETORES)


# ============================================================================
# Custom Metrics
# ============================================================================

# Track custom metrics for reporting
search_times = []
download_times = []
health_check_times = []


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track custom metrics per endpoint."""
    if name == "/api/buscar":
        search_times.append(response_time)
    elif name.startswith("/api/download"):
        download_times.append(response_time)
    elif name == "/health":
        health_check_times.append(response_time)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print custom statistics at end of test."""
    if isinstance(environment.runner, MasterRunner) or isinstance(environment.runner, WorkerRunner):
        return  # Only print on standalone or master

    print("\n" + "=" * 80)
    print("CUSTOM PERFORMANCE METRICS")
    print("=" * 80)

    if search_times:
        print("\n📊 Search Endpoint (/api/buscar):")
        print(f"   Requests: {len(search_times)}")
        print(f"   Avg: {sum(search_times) / len(search_times):.0f}ms")
        print(f"   Min: {min(search_times):.0f}ms")
        print(f"   Max: {max(search_times):.0f}ms")
        print(f"   P95: {sorted(search_times)[int(len(search_times) * 0.95)]:.0f}ms")

    if download_times:
        print("\n📦 Download Endpoint (/api/download):")
        print(f"   Requests: {len(download_times)}")
        print(f"   Avg: {sum(download_times) / len(download_times):.0f}ms")
        print(f"   Min: {min(download_times):.0f}ms")
        print(f"   Max: {max(download_times):.0f}ms")

    if health_check_times:
        print("\n💚 Health Check (/health):")
        print(f"   Requests: {len(health_check_times)}")
        print(f"   Avg: {sum(health_check_times) / len(health_check_times):.0f}ms")

    print("\n" + "=" * 80)


# ============================================================================
# Load Test User Behaviors
# ============================================================================

class BidIQUser(HttpUser):
    """
    Simulates typical BidIQ user behavior.

    Behavior pattern:
    - Check health (rare)
    - Perform searches (common)
    - Download results (after successful search)
    """

    # Wait 1-3 seconds between tasks (realistic user think time)
    wait_time = between(1, 3)

    # Store download ID for sequential download after search
    download_id = None

    @task(1)
    def health_check(self):
        """Check API health (low frequency - monitoring simulation)."""
        with self.client.get("/health", name="/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(10)
    def search_uniformes(self):
        """
        Perform search for uniformes (high frequency).

        Simulates typical user search with:
        - Random UF selection (1-5 states)
        - Last 7-30 days date range
        - Uniformes sector
        """
        # Generate search parameters
        ufs = get_random_ufs(min_count=1, max_count=3)
        data_inicial, data_final = get_date_range(days_back=random.randint(7, 30))

        payload = {
            "ufs": ufs,
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "setor": "UNIFORMES",
        }

        with self.client.post(
            "/api/buscar",
            json=payload,
            name="/api/buscar",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()

                    # Validate response structure
                    if "resumo" not in data or "oportunidades_filtradas" not in data:
                        response.failure("Invalid response structure")
                        return

                    # Store download ID for later use
                    if "download_id" in data:
                        self.download_id = data["download_id"]

                    # Log results for debugging
                    total = data.get("oportunidades_filtradas", 0)
                    print(f"   Search returned {total} opportunities")

                    response.success()

                except ValueError:
                    response.failure("Invalid JSON response")

            elif response.status_code == 422:
                # Validation error - expected occasionally
                response.success()
                print("   Validation error (expected in load test)")

            else:
                response.failure(f"Search failed: {response.status_code}")

    @task(3)
    def download_excel(self):
        """
        Download Excel report (medium frequency).

        Only executes if a previous search provided a download_id.
        """
        if not self.download_id:
            # Skip if no download ID available
            return

        download_id = self.download_id
        self.download_id = None  # Use once

        with self.client.get(
            f"/api/download?id={download_id}",
            name="/api/download",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                # Verify it's an Excel file
                content_type = response.headers.get("Content-Type", "")
                if "spreadsheet" in content_type or "excel" in content_type:
                    response.success()
                else:
                    response.failure(f"Invalid content type: {content_type}")

            elif response.status_code == 404:
                # Download ID expired or invalid (expected occasionally)
                response.success()
                print("   Download ID expired (expected)")

            else:
                response.failure(f"Download failed: {response.status_code}")


class StressTestUser(HttpUser):
    """
    Aggressive user for stress testing.

    Behavior:
    - No wait time between requests
    - Always uses maximum parameters (5 UFs, 30 day range)
    - Simulates worst-case load
    """

    wait_time = between(0, 1)  # Minimal wait time

    @task
    def aggressive_search(self):
        """Aggressive search with max parameters."""
        ufs = get_random_ufs(min_count=5, max_count=5)  # Always 5 UFs
        data_inicial, data_final = get_date_range(days_back=30)  # Always 30 days

        payload = {
            "ufs": ufs,
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "setor": "UNIFORMES",
        }

        with self.client.post("/api/buscar", json=payload, name="/api/buscar") as response:
            if response.status_code not in [200, 422, 504]:
                print(f"   Unexpected status: {response.status_code}")


# ============================================================================
# Load Test Scenarios
# ============================================================================

# Default: Use BidIQUser for realistic load testing
# Override with: locust -f locustfile.py --user-class StressTestUser

# Recommended test scenarios:
#
# 1. Smoke test (5 users, 30s):
#    locust -f locustfile.py --users 5 --spawn-rate 1 --run-time 30s --headless
#
# 2. Load test (50 users, 2min):
#    locust -f locustfile.py --users 50 --spawn-rate 5 --run-time 120s --headless
#
# 3. Stress test (100 users, 5min):
#    locust -f locustfile.py --users 100 --spawn-rate 10 --run-time 300s --headless --user-class StressTestUser
#
# 4. Endurance test (20 users, 30min):
#    locust -f locustfile.py --users 20 --spawn-rate 2 --run-time 1800s --headless
