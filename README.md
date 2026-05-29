# ECS Demo DuckDB ETL

ETL pipeline using:

* Python
* DuckDB
* Docker
* AWS ECS Fargate
* Amazon ECR
* GitHub Actions
* MySQL
* Amazon S3

The application exports data from MySQL to Parquet files stored in S3 using DuckDB.

---

# Architecture

MySQL → DuckDB → Parquet → Amazon S3

Deployment flow:

GitHub → GitHub Actions → Amazon ECR → Amazon ECS Fargate

---

# Project Structure

```text
ECS-DEMO-DUCKDB
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── .env
├── .gitignore
├── Dockerfile
├── main.py
├── README.md
└── requirements.txt
```

---

# Local Development

## Requirements

* Python 3.11+
* Docker
* AWS CLI
* AWS Account

---

# Environment Variables

Create `.env` file for local testing:

```env
DB_HOST=1.11.111.11
DB_USER=user
DB_PASSWORD=user_password
DB_NAME=your_database
```

---

# Application Code

## main.py

Main ETL process:

* Connects to MySQL
* Reads table using DuckDB MySQL extension
* Exports data to S3 as Parquet

Output file:

```text
s3://s3-mw-snowflake/output/new_forecast_details_data.parquet
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Run Locally

```bash
docker build -t duckdb-etl .
```

```bash
docker run --rm \
  --env-file .env \
  -v ~/.aws:/root/.aws:ro \
  duckdb-etl
```

---

# Docker Configuration

## Dockerfile

Uses:

* python:3.11-slim
* DuckDB
* MySQL extension
* httpfs extension

The container automatically runs:

```bash
python main.py
```

---

# AWS Configuration

## 1. Create IAM User

Create IAM user:

```text
s3-duckdb
```

AWS Console:

IAM → Users

Generate:

* Access Key
* Secret Access Key

Use case:

```text
Third-party service
```

---

# Required IAM Policies

Attach AWS managed policies:

* AmazonEC2ContainerRegistryFullAccess
* AmazonEC2ContainerRegistryPowerUser
* AmazonEC2ContainerRegistryPullOnly
* CloudWatchLogsFullAccess

---

# Custom IAM Policy

## iam:PassRole

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": [
        "arn:aws:iam::111111111111:role/s3-mw-snowflake",
        "arn:aws:iam::111111111111:role/ecsTaskExecutionRoleNew"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "ecs-tasks.amazonaws.com"
        }
      }
    }
  ]
}
```

---

# ECS Task Role Policy

Policy attached to:

```text
s3-mw-snowflake
```

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::111111111111:role/ecsTaskExecutionRole"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion"
      ],
      "Resource": "arn:aws:s3:::s3-mw-snowflake/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::s3-mw-snowflake"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService",
        "ecs:DescribeServices"
      ],
      "Resource": "*"
    }
  ]
}
```

---

# Create Amazon ECR Repository

Create repository:

```text
etl-duckdb
```

Example:

```text
111111111111.dkr.ecr.us-east-1.amazonaws.com/etl-duckdb
```

---

# Create ECS Cluster

Create cluster:

```text
duckdb-cluster
```

Use:

* Amazon ECS
* Fargate

---

# Create ECS Task Definition

Task name:

```text
duckdb-etl-task
```

Task definition example:

```json
{
  "family": "duckdb-etl-task",
  "containerDefinitions": [
    {
      "name": "etl-container",
      "image": "111111111111.dkr.ecr.us-east-1.amazonaws.com/etl-duckdb:latest",
      "cpu": 0,
      "memory": 2048,
      "essential": true,

      "environment": [
        {
          "name": "DB_NAME",
          "value": "big_pharma"
        }
      ],

      "secrets": [
        {
          "name": "DB_HOST",
          "valueFrom": "arn:aws:ssm:us-east-1:111111111111:parameter/db_host"
        },
        {
          "name": "DB_USER",
          "valueFrom": "arn:aws:ssm:us-east-1:111111111111:parameter/db_user"
        },
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:ssm:us-east-1:111111111111:parameter/db_password"
        }
      ],

      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/duckdb-etl",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],

  "taskRoleArn": "arn:aws:iam::111111111111:role/s3-mw-snowflake",
  "executionRoleArn": "arn:aws:iam::111111111111:role/ecsTaskExecutionRoleNew",

  "networkMode": "awsvpc",

  "requiresCompatibilities": [
    "FARGATE"
  ],

  "cpu": "1024",
  "memory": "2048"
}
```

---

# Create SSM Parameters

AWS Console:

Systems Manager → Parameter Store

Create parameters:

```text
db_host
db_user
db_password
```

---

# Create CloudWatch Log Group

Create log group:

```text
/ecs/duckdb-etl
```

AWS Console:

CloudWatch → Log Groups

---

# GitHub Secrets

In GitHub repository:

Settings → Secrets and variables → Actions

Create:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
ECR_REPOSITORY
```

Example:

```text
AWS_REGION=us-east-1
ECR_REPOSITORY=etl-duckdb
```

---

# GitHub Actions Deployment

Every push to `main` branch:

1. Builds Docker image
2. Pushes image to ECR
3. Updates ECS task definition
4. Deploys new ECS revision

---

# Push Changes to GitHub

```bash
git add .
```

```bash
git commit -m "deploy ecs etl"
```

```bash
git push origin main
```

GitHub Actions automatically starts deployment.

---

# Verify Deployment

## Amazon ECR

Check if image exists:

```text
etl-duckdb:latest
```

---

# Amazon ECS

Check:

* Task status
* Logs
* Container health

---

# CloudWatch Logs

Open:

```text
/ecs/duckdb-etl
```

Expected logs:

```text
Connecting to MySQL...
Exporting data to S3...
Done!
```

---

# Development Database

Sample database:

```text
big_pharma
```

Download:

```text
https://github.com/mariuszwaszkuc/bigpharma/blob/main/MySql/MySqlBigPharma.7z
```

---

# Technologies

* Python
* DuckDB
* Docker
* AWS ECS
* AWS ECR
* GitHub Actions
* Amazon S3
* MySQL
* CloudWatch
* SSM Parameter Store

---
