import json

from aws_utils import AwsUtils

aws_utils = AwsUtils()
MACROPUS_WEB_DEV_CRED = json.loads(
    aws_utils.get_parameter("macropus_web_dev_service_account_cred")
)
SCPOES = ["https://www.googleapis.com/auth/calendar.readonly"]
ROO_LEAVE_CALENDAR_ID = aws_utils.get_parameter("roo_leave_id")
CALENDAR_ID = "{}@group.calendar.google.com".format(ROO_LEAVE_CALENDAR_ID)
MAXRESULTS = 100
DEV_SLACK_TOKEN = aws_utils.get_parameter("dev_slack_token")
SLACK_CHANNEL_NAME = aws_utils.get_parameter("slack_channel_name")
