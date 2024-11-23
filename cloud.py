import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def init():
    try:
        session = boto3.Session(profile_name="default")  # AWS CLI에서 설정한 프로필 사용
        ec2 = session.client("ec2", region_name="ap-northeast-2")
        return ec2
    except (NoCredentialsError, PartialCredentialsError) as e:
        print("AWS credentials are missing or incorrect:", str(e))
        return None

def list_instances(ec2):
    print("Listing instances...")
    try:
        response = ec2.describe_instances()
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                print(f"[id] {instance['InstanceId']}, "
                      f"[AMI] {instance['ImageId']}, "
                      f"[type] {instance['InstanceType']}, "
                      f"[state] {instance['State']['Name']}, "
                      f"[monitoring state] {instance['Monitoring']['State']}")
    except Exception as e:
        print(f"Error listing instances: {str(e)}")

def available_zones(ec2):
    print("Available zones...")
    try:
        response = ec2.describe_availability_zones()
        for zone in response.get("AvailabilityZones", []):
            print(f"[id] {zone['ZoneId']}, [region] {zone['RegionName']}, [zone] {zone['ZoneName']}")
    except Exception as e:
        print(f"Error retrieving zones: {str(e)}")

def start_instance(ec2, instance_id):
    print(f"Starting instance {instance_id}...")
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"Successfully started instance {instance_id}")
    except Exception as e:
        print(f"Error starting instance: {str(e)}")

def available_regions(ec2):
    print("Available regions...")
    try:
        regions = ec2.describe_regions()
        for region in regions["Regions"]:
            print(f"[region] {region['RegionName']}, [endpoint] {region['Endpoint']}")
    except Exception as e:
        print(f"Error retrieving regions: {str(e)}")

def stop_instance(ec2, instance_id):
    print(f"Stopping instance {instance_id}...")
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"Successfully stopped instance {instance_id}")
    except Exception as e:
        print(f"Error stopping instance: {str(e)}")

def create_instance(ec2, ami_id):
    print(f"Creating instance with AMI {ami_id}...")
    try:
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType="t2.micro",
            MinCount=1,
            MaxCount=1
        )
        instance_id = response["Instances"][0]["InstanceId"]
        print(f"Successfully created instance {instance_id} based on AMI {ami_id}")
    except Exception as e:
        print(f"Error creating instance: {str(e)}")

def reboot_instance(ec2, instance_id):
    print(f"Rebooting instance {instance_id}...")
    try:
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f"Successfully rebooted instance {instance_id}")
    except Exception as e:
        print(f"Error rebooting instance: {str(e)}")

def list_images(ec2):
    print("Listing images...")
    try:
        response = ec2.describe_images(Filters=[{"Name": "name", "Values": ["htcondor-slave-image"]}])
        for image in response["Images"]:
            print(f"[ImageID] {image['ImageId']}, [Name] {image['Name']}, [Owner] {image['OwnerId']}")
    except Exception as e:
        print(f"Error listing images: {str(e)}")

def main():
    ec2 = init()
    if not ec2:
        return

    while True:
        print("\n------------------------------------------------------------")
        print("           Amazon AWS Control Panel using SDK               ")
        print("------------------------------------------------------------")
        print("  1. List instances              2. Available zones         ")
        print("  3. Start instance              4. Available regions       ")
        print("  5. Stop instance               6. Create instance         ")
        print("  7. Reboot instance             8. List images             ")
        print("                                 99. Quit                   ")
        print("------------------------------------------------------------")

        choice = input("Enter an integer: ").strip()
        if choice == "1":
            list_instances(ec2)
        elif choice == "2":
            available_zones(ec2)
        elif choice == "3":
            instance_id = input("Enter instance ID: ").strip()
            start_instance(ec2, instance_id)
        elif choice == "4":
            available_regions(ec2)
        elif choice == "5":
            instance_id = input("Enter instance ID: ").strip()
            stop_instance(ec2, instance_id)
        elif choice == "6":
            ami_id = input("Enter AMI ID: ").strip()
            create_instance(ec2, ami_id)
        elif choice == "7":
            instance_id = input("Enter instance ID: ").strip()
            reboot_instance(ec2, instance_id)
        elif choice == "8":
            list_images(ec2)
        elif choice == "99":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()
