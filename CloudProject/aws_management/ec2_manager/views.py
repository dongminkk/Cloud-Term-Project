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
    

# 인스턴스 목록 조회 뷰
def list_instances(request):
    ec2 = init_ec2()
    if not ec2:
        return render(request, "error.html", {"message": "AWS 자격 증명이 없거나 잘못되었습니다."})

    try:
        response = ec2.describe_instances()
        instances = [
            {
                "id": i["InstanceId"],
                "type": i["InstanceType"],
                "state": i["State"]["Name"],
                "ami": i["ImageId"]
            }
            for r in response.get("Reservations", [])
            for i in r.get("Instances", [])
        ]
        return render(request, "ec2_manager/list_instances.html", {"instances": instances})
    except Exception as e:
        return render(request, "error.html", {"message": str(e)})

