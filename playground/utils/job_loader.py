import json
from pathlib import Path
from typing import Dict


JOBS_DIR = Path(__file__).parent.parent.parent / "requests/jobs"


class JobLoader:
    @staticmethod
    def load_job(job_key: str) -> Dict:
        file_path = JOBS_DIR / f"{job_key}.json"

        try:
            with open(file_path, "r") as f:
                job_data = json.load(f)
                return job_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON file {file_path}: {e}")
        except IOError:
            raise ValueError(f"Job '{job_key}.json' not found in jobs folder")
