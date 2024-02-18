import boto3

session = boto3.Session(profile_name="sigrun")
ec2 = session.resource("ec2")
