"""
HTTP Playground

This playground simulates sending jobs to the API via HTTP requests,
performs polling to check the status, and displays the results.
Similar to the examples.http file but as a Python script.
"""

import json
import time
from typing import Dict, Optional

import httpx


class HTTPPlayground:
    """Client for testing the job API with polling support."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        """Initialize the HTTP playground client.

        Args:
            base_url: Base URL of the API server
        """
        self.base_url = base_url
        self.jobs_endpoint = f"{base_url}/jobs"

    def submit_job(self, job_type: str, job_data: Dict) -> Optional[Dict]:
        """Submit a job to the API.

        Args:
            job_type: The type of job to submit (determines endpoint)
            job_data: The job data to submit (without job_type field)

        Returns:
            Response data with job_id, status, and message
        """
        endpoint = f"{self.jobs_endpoint}/{job_type}"
        print(f"Submitting job to {endpoint}")
        print(f"Job data: {json.dumps(job_data, indent=2)}")
        print()

        try:
            response = httpx.post(
                endpoint,
                json=job_data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            result = response.json()
            print("Job submitted successfully!")
            print(f"Job ID: {result['job_id']}")
            print(f"Status: {result['status']}")
            print(f"Message: {result['message']}")
            print()

            return result

        except httpx.ConnectError:
            print("Error: Could not connect to the API server")
            print(f"Make sure the server is running at {self.base_url}")
            return None
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get the status of a job.

        Args:
            job_id: The ID of the job to check

        Returns:
            Job status data including result if completed
        """
        try:
            response = httpx.get(f"{self.jobs_endpoint}/{job_id}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print(f"Job {job_id} not found")
            else:
                print(f"HTTP Error: {e}")
            return None
        except Exception as e:
            print(f"Error getting job status: {e}")
            return None

    def poll_job(
        self,
        job_id: str,
        max_attempts: int = 30,
        interval: int = 2,
    ) -> Optional[Dict]:
        """Poll a job until it completes or max attempts is reached.

        Args:
            job_id: The ID of the job to poll
            max_attempts: Maximum number of polling attempts
            interval: Seconds to wait between attempts

        Returns:
            Final job status data
        """
        print(f"Polling job {job_id}...")
        print(f"Max attempts: {max_attempts}, Interval: {interval}s")
        print()

        for attempt in range(1, max_attempts + 1):
            status_data = self.get_job_status(job_id)

            if not status_data:
                return None

            status = status_data.get("status")
            print(f"Attempt {attempt}/{max_attempts} - Status: {status}")

            if status in ["completed", "failed"]:
                print()
                return status_data

            time.sleep(interval)

        print()
        print(f"Polling timeout after {max_attempts} attempts")
        return status_data

    def display_result(self, job_data: Dict) -> None:
        """Display the final job result in a formatted way.

        Args:
            job_data: The complete job data including result
        """
        print("=" * 60)
        print("JOB RESULT")
        print("=" * 60)
        print(f"Job ID: {job_data['job_id']}")
        print(f"Job Type: {job_data['job_type']}")
        print(f"Status: {job_data['status']}")
        print()

        if job_data.get("created_at"):
            print(f"Created at: {job_data['created_at']}")
        if job_data.get("started_at"):
            print(f"Started at: {job_data['started_at']}")
        if job_data.get("completed_at"):
            print(f"Completed at: {job_data['completed_at']}")
            print()

        if job_data["status"] == "completed" and job_data.get("result"):
            print("Result:")
            print(json.dumps(job_data["result"], indent=2))
        elif job_data["status"] == "failed" and job_data.get("error"):
            print(f"Error: {job_data['error']}")

        print("=" * 60)

    def run_example(self, job_type: str, job_data: Dict) -> None:
        """Run a complete example: submit, poll, and display results.

        Args:
            job_type: The type of job to submit
            job_data: The job data to submit (without job_type field)
        """
        print("HTTP Playground - Job Processing Demo")
        print("=" * 60)
        print()

        # Submit job
        submission_result = self.submit_job(job_type, job_data)
        if not submission_result:
            return

        job_id = submission_result["job_id"]

        # Poll for completion
        final_status = self.poll_job(job_id)
        if not final_status:
            return

        # Display results
        self.display_result(final_status)


def main():
    """Main entry point for the HTTP playground."""
    # Create client
    client = HTTPPlayground(base_url="http://127.0.0.1:8080")

    # Define job data (without job_type - it's in the URL now)
    job_data = {
        "message": "Hello, World! This is a test message.",
        "metadata": {"source": "http-playground", "test": True},
    }

    # Run example workflow
    client.run_example(job_type="example", job_data=job_data)


if __name__ == "__main__":
    main()
