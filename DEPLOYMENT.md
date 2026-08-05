# PIB Daily Tracker - Deployment Guide

This guide covers deploying PIB Daily Tracker on different platforms.

## Table of Contents

1. [Local Machine](#local-machine)
2. [GitHub Actions (Automated)](#github-actions-automated)
3. [Docker](#docker)
4. [Cloud Platforms](#cloud-platforms)
   - [Heroku](#heroku)
   - [AWS Lambda](#aws-lambda)
   - [Google Cloud Run](#google-cloud-run)
5. [Linux Server (VPS)](#linux-server-vps)

---

## Local Machine

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/27anushkasingh/pib-daily-tracker.git
   cd pib-daily-tracker
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (optional)
   ```

5. **Run the tracker:**
   ```bash
   # Generate digest for today
   python main.py generate
   
   # Or start scheduler (runs at 8 PM daily)
   python main.py schedule
   ```

6. **View digests:**
   - Digests are saved in `data/daily_digests/`
   - Format: `YYYY-MM-DD_pib_digest.md`

---

## GitHub Actions (Automated)

Automatically generate digests daily using GitHub Actions.

### Steps

1. **Create workflow directory:**
   ```bash
   mkdir -p .github/workflows
   ```

2. **Create workflow file:**

Create `.github/workflows/daily-digest.yml`:

```yaml
name: PIB Daily Digest

on:
  schedule:
    # Run at 8 PM IST (2:30 PM UTC)
    - cron: '30 14 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  generate-digest:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Generate digest
        run: python main.py generate
      
      - name: Commit and push digest
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/daily_digests/
          git commit -m "Daily PIB digest - $(date +'%Y-%m-%d')" || echo "No changes"
          git push
```

3. **Enable GitHub Actions:**
   - Go to repository **Settings** → **Actions** → **General**
   - Enable **Actions**

4. **Grant permissions (if needed):**
   - Settings → **Code and automation** → **Actions** → **General**
   - Set **Workflow permissions** to "Read and write permissions"

5. **Verify:**
   - Go to **Actions** tab
   - Check workflow runs
   - Digests auto-commit to `data/daily_digests/`

---

## Docker

Deploy using Docker containerization.

### Create Dockerfile

Create `Dockerfile` in repository root:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium-browser \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/daily_digests data/cache logs

# Run application
CMD ["python", "main.py", "schedule"]
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  pib-tracker:
    build: .
    container_name: pib-daily-tracker
    environment:
      - PIB_DIGEST_TIME=20:00
      - LOG_LEVEL=INFO
      - TIMEZONE=Asia/Kolkata
      # - OPENAI_API_KEY=your-key-here  # Optional
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: always
```

### Deploy

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f pib-tracker

# Stop
docker-compose down
```

---

## Cloud Platforms

### Heroku

**Prerequisites:**
- Heroku account
- Heroku CLI installed

**Steps:**

1. **Login to Heroku:**
   ```bash
   heroku login
   ```

2. **Create app:**
   ```bash
   heroku create pib-daily-tracker
   ```

3. **Create Procfile** in repository root:
   ```
   worker: python main.py schedule
   ```

4. **Create runtime.txt:**
   ```
   python-3.10.13
   ```

5. **Deploy:**
   ```bash
   git push heroku main
   ```

6. **Scale worker dyno:**
   ```bash
   heroku ps:scale worker=1
   ```

7. **View logs:**
   ```bash
   heroku logs --tail
   ```

**Note:** Heroku free tier is no longer available. Use paid dynos or alternative platforms.

---

### AWS Lambda

Deploy as serverless function for periodic execution.

**Prerequisites:**
- AWS account
- AWS CLI configured
- SAM (Serverless Application Model) installed

**Steps:**

1. **Create SAM template** (`template.yaml`):

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 300
    MemorySize: 512
    Runtime: python3.10
    Environment:
      Variables:
        LOG_LEVEL: INFO

Resources:
  PIBTrackerFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: pib-daily-tracker
      CodeUri: .
      Handler: lambda_handler.lambda_handler
      Events:
        DailySchedule:
          Type: Schedule
          Properties:
            Schedule: 'cron(30 14 * * ? *)'  # 8 PM IST = 2:30 PM UTC
      Policies:
        - S3CrudPolicy:
            BucketName: !Ref DigestBucket

  DigestBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: pib-daily-tracker-digests

Outputs:
  FunctionArn:
    Value: !GetAtt PIBTrackerFunction.Arn
  BucketName:
    Value: !Ref DigestBucket
```

2. **Create `lambda_handler.py`:**

```python
import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import generate_digest

def lambda_handler(event, context):
    """AWS Lambda handler."""
    try:
        filepath = generate_digest()
        return {
            'statusCode': 200,
            'body': f'Digest generated: {filepath}'
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }
```

3. **Build and deploy:**
   ```bash
   sam build
   sam deploy --guided
   ```

4. **View logs:**
   ```bash
   aws logs tail /aws/lambda/pib-daily-tracker --follow
   ```

---

### Google Cloud Run

Deploy as containerized service.

**Prerequisites:**
- Google Cloud account
- `gcloud` CLI installed
- Project set up

**Steps:**

1. **Build image:**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/pib-daily-tracker
   ```

2. **Deploy:**
   ```bash
   gcloud run deploy pib-daily-tracker \
     --image gcr.io/PROJECT_ID/pib-daily-tracker \
     --platform managed \
     --region us-central1 \
     --memory 512Mi \
     --set-env-vars "TIMEZONE=Asia/Kolkata,LOG_LEVEL=INFO"
   ```

3. **Schedule with Cloud Scheduler:**
   ```bash
   gcloud scheduler jobs create app-engine pib-digest \
     --schedule="30 14 * * *" \
     --http-method=POST \
     --uri="https://your-cloud-run-url/generate"
   ```

---

## Linux Server (VPS)

Deploy on a Linux VPS (DigitalOcean, Linode, etc.).

### Prerequisites
- Linux server (Ubuntu 20.04+)
- SSH access
- Root or sudo privileges

### Steps

1. **SSH into server:**
   ```bash
   ssh root@your_server_ip
   ```

2. **Update system:**
   ```bash
   apt update && apt upgrade -y
   ```

3. **Install dependencies:**
   ```bash
   apt install -y python3.10 python3-pip python3-venv git
   ```

4. **Clone repository:**
   ```bash
   cd /opt
   git clone https://github.com/27anushkasingh/pib-daily-tracker.git
   cd pib-daily-tracker
   ```

5. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```

6. **Create systemd service** (`/etc/systemd/system/pib-tracker.service`):

```ini
[Unit]
Description=PIB Daily Tracker
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/pib-daily-tracker
ExecStart=/opt/pib-daily-tracker/venv/bin/python main.py schedule
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

7. **Enable and start service:**
   ```bash
   systemctl daemon-reload
   systemctl enable pib-tracker
   systemctl start pib-tracker
   systemctl status pib-tracker
   ```

8. **View logs:**
   ```bash
   journalctl -u pib-tracker -f
   tail -f /opt/pib-daily-tracker/logs/pib_tracker.log
   ```

9. **Setup log rotation** (`/etc/logrotate.d/pib-tracker`):

```
/opt/pib-daily-tracker/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

---

## Monitoring & Maintenance

### Check Service Status
```bash
systemctl status pib-tracker
```

### View Logs
```bash
tail -f /opt/pib-daily-tracker/logs/pib_tracker.log
```

### Update Application
```bash
cd /opt/pib-daily-tracker
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart pib-tracker
```

### Backup Digests
```bash
tar -czf digests_backup_$(date +%Y%m%d).tar.gz data/daily_digests/
```

---

## Recommended Setup for Production

**Best option for PIB Daily Tracker:**

1. **GitHub Actions** (Easiest)
   - Free, no infrastructure costs
   - Auto-commits digests to repository
   - Best for simple use cases

2. **Docker on VPS** (Flexible)
   - Full control over environment
   - Easy to scale
   - More complex setup

3. **AWS Lambda** (Serverless)
   - Pay only for execution
   - Automatic scaling
   - Best for variable load

---

## Troubleshooting

### Issue: Digest not generating
- Check logs: `tail -f logs/pib_tracker.log`
- Verify PIB website is accessible
- Check `DIGEST_TIME` in `.env`

### Issue: Old Python version
```bash
# Check version
python3 --version

# Install Python 3.10
apt install -y python3.10
```

### Issue: Memory issues
- Increase container memory
- Reduce `MAX_RETRIES` in `.env`
- Optimize Selenium browser settings

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/27anushkasingh/pib-daily-tracker/issues
- Logs: Check `logs/pib_tracker.log`
- Configuration: Review `.env` settings
