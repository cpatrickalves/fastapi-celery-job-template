"""
HTTP Playground

This playground simulates sending events to the API via HTTP requests,
performs polling to check the status, and displays the results.
Similar to the examples.http file but as a Python script.
"""

import json
import time
from typing import Dict, Optional

import httpx


class HTTPPlayground:
    """Client for testing the event API with polling support."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        """Initialize the HTTP playground client.

        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.events_endpoint = f"{base_url}/events"

    def submit_event(self, event_data: Dict) -> Optional[Dict]:
        """Submit an event to the API.

        Args:
            event_data: The event data to submit

        Returns:
            Response data with event_id, status, and message
        """
        print(f"📤 Submitting event to {self.events_endpoint}")
        print(f"Event data: {json.dumps(event_data, indent=2)}")
        print()

        try:
            response = httpx.post(
                self.events_endpoint,
                json=event_data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()
            print(f"✅ Event submitted successfully!")
            print(f"Event ID: {result['event_id']}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print()

            return result

        except httpx.ConnectError:
            print("❌ Error: Could not connect to the API server")
            print(f"Make sure the server is running at {self.base_url}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None

    def get_event_status(self, event_id: str) -> Optional[Dict]:
        """Get the status of an event.

        Args:
            event_id: The ID of the event to check

        Returns:
            Event status data including result if completed
        """
        try:
            response = httpx.get(f"{self.events_endpoint}/{event_id}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"❌ Event {event_id} not found")
            else:
                print(f"❌ HTTP Error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error getting event status: {e}")
            return None

    def poll_event(
        self,
        event_id: str,
        max_attempts: int = 30,
        interval: int = 2,
    ) -> Optional[Dict]:
        """Poll an event until it completes or max attempts is reached.

        Args:
            event_id: The ID of the event to poll
            max_attempts: Maximum number of polling attempts
            interval: Seconds to wait between attempts

        Returns:
            Final event status data
        """
        print(f"🔄 Polling event {event_id}...")
        print(f"Max attempts: {max_attempts}, Interval: {interval}s")
        print()

        for attempt in range(1, max_attempts + 1):
            status_data = self.get_event_status(event_id)

            if not status_data:
                return None

            status = status_data.get("status")
            print(f"Attempt {attempt}/{max_attempts} - Status: {status}")

            if status in ["completed", "failed"]:
                print()
                return status_data

            time.sleep(interval)

        print()
        print(f"⚠️  Polling timeout after {max_attempts} attempts")
        return status_data

    def display_result(self, event_data: Dict) -> None:
        """Display the final event result in a formatted way.

        Args:
            event_data: The complete event data including result
        """
        print("=" * 60)
        print("EVENT RESULT")
        print("=" * 60)
        print(f"Event ID: {event_data['event_id']}")
        print(f"Event Type: {event_data['event_type']}")
        print(f"Status: {event_data['status']}")
        print()

        if event_data.get("created_at"):
            print(f"Created at: {event_data['created_at']}")
        if event_data.get("started_at"):
            print(f"Started at: {event_data['started_at']}")
        if event_data.get("completed_at"):
            print(f"Completed at: {event_data['completed_at']}")
            print()

        if event_data["status"] == "completed" and event_data.get("result"):
            print("Result:")
            print(json.dumps(event_data["result"], indent=2))
        elif event_data["status"] == "failed" and event_data.get("error"):
            print(f"Error: {event_data['error']}")

        print("=" * 60)

    def run_example(self, event_data: Dict) -> None:
        """Run a complete example: submit, poll, and display results.

        Args:
            event_data: The event data to submit (dict with event_type, message, etc.)
        """
        print("🚀 HTTP Playground - Event Processing Demo")
        print("=" * 60)
        print()

        # Submit event
        submission_result = self.submit_event(event_data)
        if not submission_result:
            return

        event_id = submission_result["event_id"]

        # Poll for completion
        final_status = self.poll_event(event_id)
        if not final_status:
            return

        # Display results
        self.display_result(final_status)


def main():
    """Main entry point for the HTTP playground."""
    # Create client
    client = HTTPPlayground(base_url="http://127.0.0.1:8080")

    # Define event data directly (like in examples.http)
    event_data = {
        "event_type": "example",
        "message": "Hello, World! This is a test message.",
        "metadata": {"source": "http-playground", "test": True},
    }

    # Run example workflow
    client.run_example(event_data)


if __name__ == "__main__":
    main()
