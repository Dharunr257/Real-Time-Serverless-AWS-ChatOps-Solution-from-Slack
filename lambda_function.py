import json
import base64
from urllib.parse import parse_qs
from datetime import datetime, timedelta, date
import hmac
import hashlib
import time
import boto3

# ==================================================
# CONFIGURATION
# ==================================================

INSTANCE_ID = "i-04e64152e23a*****" # replace it with ur ec2 instance id

ec2 = boto3.client("ec2")

cloudwatch = boto3.client(
    "cloudwatch"
)

cost_explorer = boto3.client(
    "ce",
    region_name="us-east-1"
)

secretsmanager = boto3.client(
    "secretsmanager"
)

# ==================================================
# SECRETS MANAGER
# ==================================================

def get_slack_secret():

    response = secretsmanager.get_secret_value(
        SecretId="aws-chatops/slack"
    )

    secret = json.loads(
        response["SecretString"]
    )

    return secret["SLACK_SIGNING_SECRET"]


# ==================================================
# SLACK SIGNATURE VALIDATION
# ==================================================

def verify_slack_request(event):

    headers = event["headers"]

    slack_signature = headers.get(
        "x-slack-signature"
    )

    slack_timestamp = headers.get(
        "x-slack-request-timestamp"
    )

    if not slack_signature or not slack_timestamp:
        return False

    # Replay Attack Protection

    if abs(
        time.time() - int(slack_timestamp)
    ) > 300:
        return False

    body = event["body"]

    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(
            body
        ).decode("utf-8")
    else:
        raw_body = body

    secret = get_slack_secret()

    sig_basestring = (
        f"v0:{slack_timestamp}:{raw_body}"
    )

    my_signature = (
        "v0="
        + hmac.new(
            secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
    )

    return hmac.compare_digest(
        my_signature,
        slack_signature
    )


# ==================================================
# RESPONSE HELPER
# ==================================================

def slack_response(message):

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "response_type": "in_channel",
            "text": message
        })
    }


# ==================================================
# STATUS DASHBOARD
# ==================================================

def get_status():

    response = ec2.describe_instances(
        InstanceIds=[INSTANCE_ID]
    )

    instance = response["Reservations"][0]["Instances"][0]

    state = instance["State"]["Name"]

    instance_type = instance["InstanceType"]

    public_ip = instance.get(
        "PublicIpAddress",
        "Not Available"
    )

    private_ip = instance.get(
        "PrivateIpAddress",
        "Not Available"
    )

    availability_zone = instance["Placement"][
        "AvailabilityZone"
    ]

    launch_time = instance[
        "LaunchTime"
    ].strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    instance_name = "Unknown"

    if "Tags" in instance:

        for tag in instance["Tags"]:

            if tag["Key"] == "Name":

                instance_name = tag["Value"]

                break

    return slack_response(
        f"📊 AWS Infrastructure Dashboard\n\n"
        f"🏷 Name: {instance_name}\n"
        f"🆔 Instance ID: {INSTANCE_ID}\n\n"
        f"🟢 State: {state}\n"
        f"🖥 Type: {instance_type}\n\n"
        f"🌍 Availability Zone: {availability_zone}\n"
        f"🔒 Private IP: {private_ip}\n"
        f"🌐 Public IP: {public_ip}\n\n"
        f"⏰ Launch Time: {launch_time}\n\n"
        f"✅ Security Status: Verified"
    )


# ==================================================
# START SERVER
# ==================================================

def start_server():

    response = ec2.start_instances(
        InstanceIds=[INSTANCE_ID]
    )

    current_state = (
        response["StartingInstances"][0]
        ["CurrentState"]["Name"]
    )

    return slack_response(
        f"🚀 Infrastructure Operation\n\n"
        f"Action: Start Instance\n"
        f"Instance ID: {INSTANCE_ID}\n"
        f"Current State: {current_state}\n\n"
        f"✅ Request Successfully Submitted"
    )


# ==================================================
# STOP SERVER
# ==================================================

def stop_server():

    response = ec2.stop_instances(
        InstanceIds=[INSTANCE_ID]
    )

    current_state = (
        response["StoppingInstances"][0]
        ["CurrentState"]["Name"]
    )

    return slack_response(
        f"🛑 Infrastructure Operation\n\n"
        f"Action: Stop Instance\n"
        f"Instance ID: {INSTANCE_ID}\n"
        f"Current State: {current_state}\n\n"
        f"✅ Request Successfully Submitted"
    )


# ==================================================
# CLOUDWATCH DASHBOARD
# ==================================================

def get_metrics():

    end_time = datetime.utcnow()

    start_time = end_time - timedelta(
        minutes=30
    )

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": INSTANCE_ID
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=["Average"]
    )

    datapoints = response["Datapoints"]

    if not datapoints:

        return slack_response(
            "⚠️ No CloudWatch metrics available yet."
        )

    latest = sorted(
        datapoints,
        key=lambda x: x["Timestamp"]
    )[-1]

    cpu = round(
        latest["Average"],
        2
    )

    if cpu < 40:
        health = "✅ Healthy"

    elif cpu < 80:
        health = "⚠️ Moderate Load"

    else:
        health = "🚨 High CPU Usage"

    return slack_response(
        f"📈 AWS Monitoring Dashboard\n\n"
        f"🆔 Instance ID: {INSTANCE_ID}\n\n"
        f"⚡ CPU Utilization: {cpu}%\n"
        f"🏥 Health Status: {health}"
    )


# ==================================================
# COST DASHBOARD
# ==================================================

def get_aws_cost():

    today = date.today()

    first_day = today.replace(
        day=1
    )

    response = cost_explorer.get_cost_and_usage(
        TimePeriod={
            "Start": str(first_day),
            "End": str(today)
        },
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"]
    )

    amount = response["ResultsByTime"][0][
        "Total"
    ]["UnblendedCost"]["Amount"]

    amount = max(
        0,
        round(float(amount), 2)
    )

    return slack_response(
        f"💰 AWS Cost Dashboard\n\n"
        f"📅 Billing Period: Current Month\n"
        f"💵 Total Spend: ${amount:.2f}\n\n"
        f"✅ Cost Status: Within Budget"
    )


# ==================================================
# MAIN HANDLER
# ==================================================

def lambda_handler(event, context):

    try:

        if not verify_slack_request(
            event
        ):

            return {
                "statusCode": 403,
                "body": "Unauthorized"
            }

        body = event["body"]

        if event.get(
            "isBase64Encoded"
        ):

            body = base64.b64decode(
                body
            ).decode("utf-8")

        data = parse_qs(body)

        command = data.get(
            "command",
            [""]
        )[0]

        print(
            f"Received Command: {command}"
        )

        if command == "/get-status":
            return get_status()

        elif command == "/start-server":
            return start_server()

        elif command == "/stop-server":
            return stop_server()

        elif command == "/metrics":
            return get_metrics()

        elif command == "/awscost":
            return get_aws_cost()

        else:
            return slack_response(
                f"❌ Unknown Command: {command}"
            )

    except Exception as e:

        print(
            f"ERROR: {str(e)}"
        )

        return slack_response(
            f"❌ System Error\n\n{str(e)}"
        )