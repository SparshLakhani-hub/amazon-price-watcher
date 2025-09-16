from app.db import init_db
from app.scheduler import job_once

if __name__ == "__main__":
    init_db()
    job_once()
    print("Completed one scrape+alert cycle.")
