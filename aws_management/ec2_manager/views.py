from django.shortcuts import render
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# EC2 초기화 함수
def init_ec2():
    try:
        session = boto3.Session(profile_name="default")  # AWS CLI에서 설정한 프로필 사용
        ec2 = session.client("ec2", region_name="ap-northeast-2")
        return ec2
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("AWS 자격 증명이 없거나 잘못되었습니다:", str(e))
        return None
    
def ec2_operations(request):
    ec2 = init_ec2()
    if not ec2:
        return render(request, "error.html", {"message": "AWS 자격 증명이 없거나 잘못되었습니다."})

    message = None
    instances = []

    try:
        # EC2 인스턴스 목록 조회
        response = ec2.describe_instances()
        instances = [
            {
                "id": i["InstanceId"],
                "type": i["InstanceType"],
                "state": i["State"]["Name"],
                "ami": i["ImageId"],
                "public_ip": i.get("PublicIpAddress", "N/A"),  # 퍼블릭 IP가 없는 경우 처리
                "private_ip": i.get("PrivateIpAddress", "N/A"),  # 프라이빗 IP가 없는 경우 처리
                "launch_time": i["LaunchTime"].strftime("%Y-%m-%d %H:%M:%S")  # 날짜 형식 지정
            }
            for r in response.get("Reservations", [])
            for i in r.get("Instances", [])
        ]
    except Exception as e:
        return render(request, "error.html", {"message": f"인스턴스 목록 조회 중 오류 발생: {str(e)}"})

    # POST 요청 처리
    if request.method == "POST":
        action = request.POST.get("action")
        instance_id = request.POST.get("instance_id")
        tag_key = request.POST.get("tag_key")
        tag_value = request.POST.get("tag_value")

        if action == "start":
            success, msg = start_instance(ec2, instance_id)
            message = msg
        elif action == "stop":
            success, msg = stop_instance(ec2, instance_id)
            message = msg
        elif action == "terminate":
            success, msg = terminate_instance(ec2, instance_id)
            message = msg
        elif action == "status":
            describe_instance_status(ec2, instance_id)
        elif action == "tag":
            tag_instance(ec2, instance_id, tag_key, tag_value)
        elif action == "monitor":
            monitor_instance(ec2, instance_id)
        elif action == "unmonitor":
            unmonitor_instance(ec2, instance_id)
        elif action == "allocate_ip":
            ip = allocate_elastic_ip(ec2)
            message = f"Elastic IP: {ip}"

    return render(request, "ec2_manager/ec2_operations.html", {"message": message, "instances": instances})



def terminate_instance(ec2, instance_id):
    print(f"Terminating instance {instance_id}...")
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        print(f"Successfully terminated instance {instance_id}")
        return True, f"Successfully terminated instance {instance_id}"
    except Exception as e:
        print(f"Error terminating instance: {str(e)}")
        return False, f"Error terminating instance: {str(e)}"

def describe_instance_status(ec2, instance_id):
    print(f"Describing status of instance {instance_id}...")
    try:
        response = ec2.describe_instance_status(InstanceIds=[instance_id])
        statuses = response.get('InstanceStatuses', [])
        if statuses:
            status_messages = [
                f"Instance {instance_id}:"
                f"\n  Status: {status['InstanceState']['Name']}"
                f"\n  System Status: {status['SystemStatus']['Status']}"
                f"\n  Instance Status: {status['InstanceStatus']['Status']}"
                for status in statuses
            ]
            return "\n".join(status_messages)
        else:
            return f"Instance {instance_id} has no status information available."
    except Exception as e:
        print(f"Error describing instance status: {str(e)}")
        return f"Error describing instance status: {str(e)}"

def tag_instance(ec2, instance_id, tag_key, tag_value):
    print(f"Tagging instance {instance_id} with {tag_key}: {tag_value}...")
    try:
        ec2.create_tags(
            Resources=[instance_id],
            Tags=[{'Key': tag_key, 'Value': tag_value}]
        )
        print(f"Successfully tagged instance {instance_id} with {tag_key}: {tag_value}")
    except Exception as e:
        print(f"Error tagging instance: {str(e)}")

def monitor_instance(ec2, instance_id):
    print(f"Monitoring instance {instance_id}...")
    try:
        ec2.monitor_instances(InstanceIds=[instance_id])
        print(f"Successfully started monitoring instance {instance_id}")
    except Exception as e:
        print(f"Error starting monitoring: {str(e)}")

def unmonitor_instance(ec2, instance_id):
    print(f"Unmonitoring instance {instance_id}...")
    try:
        ec2.unmonitor_instances(InstanceIds=[instance_id])
        print(f"Successfully stopped monitoring instance {instance_id}")
    except Exception as e:
        print(f"Error stopping monitoring: {str(e)}")

def allocate_elastic_ip(ec2):
    print("Allocating Elastic IP...")
    try:
        allocation = ec2.allocate_address(Domain='vpc')
        print(f"Elastic IP allocated: {allocation['PublicIp']}")
        return allocation['PublicIp']
    except Exception as e:
        print(f"Error allocating Elastic IP: {str(e)}")
        return f"Error allocating Elastic IP: {str(e)}"

def start_instance(ec2, instance_id):
    print(f"Starting instance {instance_id}...")
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"Successfully started instance {instance_id}")
        return True, f"Instance {instance_id} started successfully."
    except Exception as e:
        print(f"Error starting instance: {str(e)}")
        return False, f"Error starting instance: {str(e)}"

def stop_instance(ec2, instance_id):
    print(f"Stopping instance {instance_id}...")
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"Successfully stopped instance {instance_id}")
        return True, f"Instance {instance_id} stopped successfully."
    except Exception as e:
        print(f"Error stopping instance: {str(e)}")
        return False, f"Error stopping instance: {str(e)}"