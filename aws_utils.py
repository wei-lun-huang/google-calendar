import boto3
import os


class AwsUtils:
    def __init__(self):
        self.aws_region_name = "ap-northeast-1"
        self.ssm_client = boto3.client("ssm", region_name=self.aws_region_name)
        self.ssm_root = "/gogolook/google_calendar/"

    def get_parameter(self, path):
        ret = self.ssm_client.get_parameter(
            Name=os.path.join(self.ssm_root, path), WithDecryption=True
        )

        return ret["Parameter"]["Value"]
