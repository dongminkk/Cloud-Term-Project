from django.shortcuts import render
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from django.conf import settings
import paramiko

def init_ec2():
    try:
        session = boto3.Session(profile_name="default") 
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
    condor_output = None  
    instances = []

    try:
       
        response = ec2.describe_instances()
        instances = [
            {
                "id": i["InstanceId"],
                "type": i["InstanceType"],
                "state": i["State"]["Name"],
                "ami": i["ImageId"],
                "public_ip": i.get("PublicIpAddress", "N/A"),  
                "private_ip": i.get("PrivateIpAddress", "N/A"),  
                "launch_time": i["LaunchTime"].strftime("%Y-%m-%d %H:%M:%S"), 
                "tags": {tag["Key"]: tag["Value"] for tag in i.get("Tags", [])}  
            }
            for r in response.get("Reservations", [])
            for i in r.get("Instances", [])
        ]
    except Exception as e:
        return render(request, "error.html", {"message": f"인스턴스 목록 조회 중 오류 발생: {str(e)}"})

   
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
        elif action == "tag":
            tag_instance(ec2, instance_id, tag_key, tag_value)
        elif action == "monitor":
            monitor_instance(ec2, instance_id)
        elif action == "unmonitor":
            unmonitor_instance(ec2, instance_id)
        elif action == "allocate_ip":
            ip = allocate_and_associate_elastic_ip(ec2)
            message = f"Elastic IP: {ip}"
        elif action == "reboot":  
            success, msg = reboot_instance(ec2, instance_id)
            message = msg
        elif action == "condor_status": 
            success, condor_output = condor_status_instance(ec2, instance_id)  
            if not success:
                condor_output = f"Error: {condor_output}"  
            message = "Condor 상태 조회 완료"

    return render(request, "ec2_manager/ec2_operations.html", {
        "message": message, 
        "instances": instances,
        "condor_output": condor_output  
    })


def terminate_instance(ec2, instance_id):
    print(f"Terminating instance {instance_id}...")
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        print(f"Successfully terminated instance {instance_id}")
        return True, f"Successfully terminated instance {instance_id}"
    except Exception as e:
        print(f"Error terminating instance: {str(e)}")
        return False, f"Error terminating instance: {str(e)}"


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

    print(f"Ensuring CloudWatch basic monitoring for instance {instance_id}...")
    try:
        response = ec2.describe_instance_status(InstanceIds=[instance_id])
        
        if not response["InstanceStatuses"]:
            print("인스턴스 상태 정보 없음")
            return

        instance_status = response["InstanceStatuses"][0]
        monitoring_status = instance_status.get("Monitoring", {}).get("State", "disabled")
        
        if monitoring_status == "enabled":
            print("기본 CloudWatch 모니터링은 이미 활성화되어 있습니다.")
        else:
            ec2.monitor_instances(InstanceIds=[instance_id])
            print("CloudWatch 기본 모니터링 활성화 완료")
            
    except Exception as e:
        print(f"Error enabling default CloudWatch monitoring: {str(e)}")

def unmonitor_instance(ec2, instance_id):

    print(f"Disabling CloudWatch monitoring for instance {instance_id}...")
    try:
        ec2.unmonitor_instances(InstanceIds=[instance_id])
        print(f"Successfully stopped monitoring instance {instance_id}")
    except Exception as e:
        print(f"Error stopping monitoring: {str(e)}")

def allocate_and_associate_elastic_ip(ec2, instance_id):
    print("Allocating and associating Elastic IP...")
    try:
        allocation = ec2.allocate_address(Domain='vpc')
        elastic_ip = allocation['PublicIp']
        allocation_id = allocation['AllocationId']
        print(f"Elastic IP allocated: {elastic_ip} (Allocation ID: {allocation_id})")
        
        response = ec2.associate_address(
            InstanceId=instance_id,
            AllocationId=allocation_id
        )
        association_id = response.get("AssociationId")
        print(f"Elastic IP {elastic_ip} associated with instance {instance_id}. Association ID: {association_id}")
        
        return True, f"Elastic IP {elastic_ip} successfully allocated and associated with instance {instance_id}."
    except Exception as e:
        print(f"Error allocating or associating Elastic IP: {str(e)}")
        return False, f"Error allocating or associating Elastic IP: {str(e)}"

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
    
def reboot_instance(ec2, instance_id):
    print(f"Rebooting instance {instance_id}...")
    try:
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f"Successfully rebooted instance {instance_id}")
        return True, f"Instance {instance_id} rebooted successfully."
    except Exception as e:
        print(f"Error rebooting instance: {str(e)}")
        return False, f"Error rebooting instance: {str(e)}"
    
def available_zones(request):
    ec2 = init_ec2()
    if not ec2:
        return render(request, "error.html", {"message": "AWS 자격 증명이 없거나 잘못되었습니다."})

    try:
        response = ec2.describe_availability_zones()
        zones = [
            {
                "zone_id": zone["ZoneId"],
                "region": zone["RegionName"],
                "zone_name": zone["ZoneName"]
            }
            for zone in response.get("AvailabilityZones", [])
        ]
        return render(request, "ec2_manager/available_zones.html", {"zones": zones})
    except Exception as e:
        return render(request, "error.html", {"message": f"가용 영역 조회 중 오류 발생: {str(e)}"})

def available_regions(request):
    ec2 = init_ec2()
    if not ec2:
        return render(request, "error.html", {"message": "AWS 자격 증명이 없거나 잘못되었습니다."})

    try:
        response = ec2.describe_regions()
        regions = [
            {
                "region_name": region["RegionName"],
                "endpoint": region["Endpoint"]
            }
            for region in response["Regions"]
        ]
        return render(request, "ec2_manager/available_regions.html", {"regions": regions})
    except Exception as e:
        return render(request, "error.html", {"message": f"리전 조회 중 오류 발생: {str(e)}"})

def create_and_list_images(request):
    ec2 = init_ec2()
    if not ec2:
        return render(request, "error.html", {"message": "AWS 자격 증명이 없거나 잘못되었습니다."})

   
    try:
        response = ec2.describe_images(Filters=[{"Name": "name", "Values": ["aws-htcondor-slave"]}])
        images = [
            {
                "image_id": image["ImageId"],
                "name": image.get("Name", "N/A"),
                "owner": image.get("OwnerId", "N/A")
            }
            for image in response.get("Images", [])
        ]
    except Exception as e:
        return render(request, "error.html", {"message": f"이미지 조회 중 오류 발생: {str(e)}"})

    if request.method == "POST":
        ami_id = request.POST.get("ami_id")
        try:
            response = ec2.run_instances(
                ImageId=ami_id,
                InstanceType="t2.micro",
                MinCount=1,
                MaxCount=1,
                SecurityGroupIds=["sg-0aeee0f248456bc43"]  
            )
            instance_id = response["Instances"][0]["InstanceId"]
            return render(request, "success.html", {"message": f"인스턴스가 성공적으로 생성되었습니다! 인스턴스 ID: {instance_id}"})
        except Exception as e:
            return render(request, "error.html", {"message": f"인스턴스 생성 중 오류 발생: {str(e)}"})

    return render(request, "ec2_manager/create_and_list_images.html", {"images": images})




def condor_status_instance(ec2, instance_id):
    try:
        
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance = response["Reservations"][0]["Instances"][0]
        public_ip = instance.get("PublicIpAddress")
        private_key_path = str(settings.PRIVATE_KEY_PATH)  

        if not public_ip:
            return False, "인스턴스에 퍼블릭 IP가 없습니다."

    
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  
        ssh.connect(
            hostname=public_ip,
            username="ec2-user",  
            key_filename=private_key_path  
        )

       
        stdin, stdout, stderr = ssh.exec_command("condor_status")
        output = stdout.read().decode("utf-8").strip()
        error = stderr.read().decode("utf-8").strip()
        ssh.close()

        if error:
            return False, f"명령 실행 중 오류 발생: {error}"

        if not output:
            return False, "Condor 상태 출력이 비어 있습니다."

        return True, output 

    except paramiko.AuthenticationException:
        return False, "SSH 인증 오류가 발생했습니다. 키 파일과 사용자 이름을 확인하세요."
    except paramiko.SSHException as e:
        return False, f"SSH 연결 오류: {str(e)}"
    except Exception as e:
        return False, f"condor_status 실행 중 오류 발생: {str(e)}"

