# Real-Time Serverless AWS ChatOps Solution from Slack

## End-to-End Implementation Guide

---

# Architecture Overview

This solution enables AWS infrastructure operations directly from Slack using a serverless architecture.

## Final Architecture

```text
Slack Workspace
       │
       ▼
Slack Slash Commands
       │
       ▼
Amazon API Gateway
       │
       ▼
AWS Lambda
       │
       ├── Slack Signature Verification
       ├── Replay Attack Protection
       ├── Command Routing
       │
       ├── Amazon EC2
       ├── Amazon CloudWatch
       ├── AWS Cost Explorer
       └── AWS Secrets Manager
       │
       ▼
Response Returned to Slack
```

---

# Solution Capabilities

Supported commands:

```text
/get-status
/start-server
/stop-server
/metrics
/awscost
```

Capabilities:

* Start EC2 instance
* Stop EC2 instance
* View infrastructure status
* View CPU utilization
* View monthly AWS spend
* Secure Slack request validation

---

# Prerequisites

Before starting, ensure the following:

## AWS Account

Required services:

* AWS Lambda
* API Gateway
* EC2
* CloudWatch
* Cost Explorer
* Secrets Manager
* IAM

---

## Slack Workspace

You need:

* Slack Workspace
* Permission to create Slack Apps

---

## Local Tools

Install:

```bash
aws --version
python3 --version
```

Recommended:

```text
Python 3.12+
AWS CLI v2
```

---

# Step 1 — Create EC2 Instance

This instance will be controlled from Slack.

Navigate:

```text
AWS Console
→ EC2
→ Launch Instance
```

Configuration:

```text
Name           : chatops-demo-server
AMI            : Amazon Linux 2023
Instance Type  : t3.micro
Storage        : 8 GB
```

Security Group:

```text
SSH (22) → My IP
```

Launch instance.

---

# Step 2 — Create Slack App

Navigate:

```text
https://api.slack.com/apps
```

Create:

```text
AWS ChatOps Platform
```

Select:

```text
From Scratch
```

Choose workspace.

Create App.

---

# Step 3 — Create Slash Commands

Navigate:

```text
Slack App
→ Slash Commands
```

Create:

```text
/get-status
```

Temporary Request URL:

```text
https://example.com
```

Save.

Repeat:

```text
/start-server
/stop-server
/metrics
/awscost
```

---

# Step 4 — Create Lambda Function

Navigate:

```text
AWS Console
→ Lambda
→ Create Function
```

Configuration:

```text
Name       : aws-chatops-handler
Runtime    : Python 3.12
Architecture: x86_64
```

Create Function.

---

# Step 5 — Create API Gateway

Navigate:

```text
API Gateway
→ Create API
→ HTTP API
```

Configuration:

```text
Name : aws-chatops-api
```

Integration:

```text
Lambda
→ aws-chatops-handler
```

Create.

---

# Step 6 — Create Route

Create route:

```text
POST /slack
```

Attach Lambda integration.

Deploy API.

Copy:

```text
Invoke URL
```

Example:

```text
https://xxxxx.execute-api.us-east-1.amazonaws.com
```

Final endpoint:

```text
https://xxxxx.execute-api.us-east-1.amazonaws.com/slack
```

---

# Step 7 — Update Slack Commands

Return to Slack App.

Update every slash command:

```text
/get-status
/start-server
/stop-server
/metrics
/awscost
```

Request URL:

```text
https://xxxxx.execute-api.us-east-1.amazonaws.com/slack
```

Save.

---

# Step 8 — Reinstall Slack App

Navigate:

```text
Install App
```

Click:

```text
Reinstall to Workspace
```

---

# Step 9 — Create IAM Permissions

Navigate:

```text
IAM
→ Lambda Execution Role
```

Create inline policy.

Policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "cloudwatch:GetMetricStatistics",
        "ce:GetCostAndUsage",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
```

Policy Name:

```text
ChatOpsPolicy
```

Attach policy.

---

# Step 10 — Configure Cost Explorer

Navigate:

```text
Billing
→ Cost Explorer
```

Enable:

```text
Cost Explorer
```

Wait until activation completes.

---

# Step 11 — Retrieve Slack Signing Secret

Navigate:

```text
Slack App
→ Basic Information
```

Locate:

```text
Signing Secret
```

Copy value.

---

# Step 12 — Create Secrets Manager Secret

Navigate:

```text
AWS Secrets Manager
→ Store New Secret
```

Type:

```text
Other Type of Secret
```

Key:

```text
SLACK_SIGNING_SECRET
```

Value:

```text
<Slack Signing Secret>
```

Secret Name:

```text
aws-chatops/slack
```

Create Secret.

---

# Step 13 — Implement Lambda Function

The Lambda function must implement:

## Security Layer

* Slack Signature Verification
* HMAC SHA256 Validation
* Timestamp Validation
* Replay Attack Protection

---

## Command Router

Supported routes:

```python
/get-status
/start-server
/stop-server
/metrics
/awscost
```

---

## AWS Integrations

### EC2

Operations:

```python
describe_instances()
start_instances()
stop_instances()
```

---

### CloudWatch

Operations:

```python
get_metric_statistics()
```

Metric:

```text
CPUUtilization
```

---

### Cost Explorer

Operations:

```python
get_cost_and_usage()
```

---

### Secrets Manager

Operations:

```python
get_secret_value()
```

---

# Step 14 — Deploy Lambda Code

Deploy final Lambda code.

python file available in the repo 

Verify deployment succeeds.

---

# Step 15 — Test Slack Connectivity

Execute:

```text
/get-status
```

Expected:

```text
AWS Infrastructure Dashboard
```

If successful:

```text
Slack
→ API Gateway
→ Lambda
```

is working.

---

# Step 16 — Test EC2 Operations

Stop server:

```text
/stop-server
```

Verify:

```text
EC2 State = stopped
```

Start server:

```text
/start-server
```

Verify:

```text
EC2 State = running
```

---

# Step 17 — Test Monitoring

Run:

```text
/metrics
```

Expected:

```text
CPU Utilization
Health Status
```

Note:

CloudWatch may take several minutes to publish metrics after instance startup.

---

# Step 18 — Test Cost Explorer

Run:

```text
/awscost
```

Expected:

```text
Current Month Spend
```

Example:

```text
$0.00
```

for Free Tier accounts.

---

# Step 19 — Verify Security Controls

Confirm:

```text
Slack Signature Verification
```

enabled.

Confirm:

```text
Replay Attack Protection
```

enabled.

Confirm:

```text
Secrets Manager
```

used instead of hardcoded secrets.

Confirm:

```text
Least Privilege IAM
```

implemented.

---

# Validation Checklist

## Infrastructure

```text
[ ] EC2 Instance Created
[ ] Lambda Created
[ ] API Gateway Created
[ ] Cost Explorer Enabled
[ ] Secrets Manager Configured
```

---

## Slack

```text
[ ] Slack App Created
[ ] Slash Commands Created
[ ] App Installed
```

---

## Security

```text
[ ] Signing Secret Stored
[ ] Signature Validation Working
[ ] Replay Protection Enabled
[ ] IAM Policy Attached
```

---

## Functional Testing

```text
[ ] /get-status Working
[ ] /start-server Working
[ ] /stop-server Working
[ ] /metrics Working
[ ] /awscost Working
```

---

# Final Result

You now have a fully functional serverless ChatOps solution that allows Slack users to:

* Manage EC2 instances
* Monitor infrastructure health
* View CloudWatch metrics
* Track AWS spending
* Securely perform cloud operations

using a serverless AWS architecture powered by API Gateway, Lambda, EC2, CloudWatch, Cost Explorer, Secrets Manager, and IAM.
