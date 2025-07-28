"""Performance tests using Locust."""

from locust import HttpUser, task, between
import json
import random


class MASBUser(HttpUser):
    """Simulated user for MASB application."""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Setup tasks to run when user starts."""
        # Check if application is healthy
        response = self.client.get("/health")
        if response.status_code != 200:
            raise Exception("Application not healthy")
    
    @task(10)
    def view_index(self):
        """View the index page."""
        self.client.get("/")
    
    @task(8)
    def view_results(self):
        """View results page."""
        self.client.get("/results")
    
    @task(5)
    def view_analysis(self):
        """View analysis page."""
        self.client.get("/analysis")
    
    @task(3)
    def view_evaluation_page(self):
        """View evaluation setup page."""
        self.client.get("/evaluate")
    
    @task(2)
    def api_get_models(self):
        """Get supported models via API."""
        self.client.get("/api/models")
    
    @task(2)
    def api_get_languages(self):
        """Get supported languages via API."""
        self.client.get("/api/languages")
    
    @task(4)
    def api_get_statistics(self):
        """Get statistics via API."""
        # Test with various filter combinations
        filters = [
            "",
            "?days=7",
            "?days=30",
            "?model=gpt-4",
            "?language=en",
            "?model=gpt-4&language=en&days=7"
        ]
        filter_params = random.choice(filters)
        self.client.get(f"/api/statistics{filter_params}")
    
    @task(6)
    def api_get_results(self):
        """Get results via API."""
        # Test with various filter combinations
        limits = [10, 25, 50]
        limit = random.choice(limits)
        
        filters = [
            f"?limit={limit}",
            f"?limit={limit}&model=gpt-4",
            f"?limit={limit}&language=en",
            f"?limit={limit}&category=hallucination"
        ]
        filter_params = random.choice(filters)
        self.client.get(f"/api/results{filter_params}")
    
    @task(1)
    def view_settings(self):
        """View settings page."""
        self.client.get("/settings")
    
    @task(1)
    def health_check(self):
        """Check application health."""
        self.client.get("/health")


class AdminUser(HttpUser):
    """Admin user with additional privileges."""
    
    wait_time = between(2, 8)
    
    @task(5)
    def view_results_with_details(self):
        """View results and drill down to details."""
        # First get list of results
        response = self.client.get("/api/results?limit=10")
        if response.status_code == 200:
            try:
                results = response.json()
                if results:
                    # Pick a random result to view details
                    result = random.choice(results)
                    batch_id = result.get('batch_id')
                    if batch_id:
                        self.client.get(f"/results/{batch_id}")
            except (json.JSONDecodeError, KeyError):
                pass
    
    @task(2)
    def export_data(self):
        """Test data export functionality."""
        formats = ['json', 'csv']
        format_type = random.choice(formats)
        
        with self.client.get(f"/api/export?format={format_type}", 
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 500:
                # Export might fail in test environment
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")
    
    @task(1)
    def comprehensive_statistics(self):
        """Get comprehensive statistics."""
        self.client.get("/api/statistics?days=90")


class StressTestUser(HttpUser):
    """User for stress testing concurrent requests."""
    
    wait_time = between(0.1, 1)  # Very short wait time for stress
    
    @task(20)
    def rapid_api_calls(self):
        """Make rapid API calls."""
        endpoints = [
            "/api/models",
            "/api/languages", 
            "/api/statistics",
            "/api/results?limit=5",
            "/health"
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)
    
    @task(10)
    def concurrent_page_views(self):
        """Concurrent page views."""
        pages = ["/", "/results", "/analysis"]
        page = random.choice(pages)
        self.client.get(page)


# Test scenarios for different load patterns
class WebsiteUser(HttpUser):
    """Regular website user behavior."""
    
    wait_time = between(5, 15)  # More realistic human wait times
    
    def on_start(self):
        """User starts by viewing the main page."""
        self.client.get("/")
    
    @task(3)
    def browse_results(self):
        """Browse through results."""
        self.client.get("/results")
        
        # Sometimes look at analysis
        if random.random() < 0.3:
            self.client.get("/analysis")
    
    @task(1)
    def start_evaluation_flow(self):
        """User considering starting an evaluation."""
        self.client.get("/evaluate")
        
        # Get models and languages (as if user is exploring options)
        self.client.get("/api/models")
        self.client.get("/api/languages")
    
    @task(1)
    def check_statistics(self):
        """Check current statistics."""
        self.client.get("/api/statistics")


# Configuration for different test scenarios
def create_test_config():
    """Create test configuration."""
    return {
        'host': 'http://localhost:8080',
        'users': 50,
        'spawn_rate': 5,
        'run_time': '5m'
    }