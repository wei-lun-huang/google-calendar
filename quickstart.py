import datetime
import json
import os.path
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from aws_utils import AwsUtils
from slack_utils import SlackMessage


class GoogleCalendar:
    def __init__(
        self, scopes, calendar_id, maxResults, slack_utils, slack_webhook=None
    ):
        # If modifying these scopes, delete the file token.json.
        self.scopes = scopes
        self.calendar_id = calendar_id
        self.maxResults = maxResults
        self.slack_webhook = slack_webhook
        self.slack_utils = slack_utils
        self.credentials = "credentials.json"
        self.token_file = "token.json"
        self.now = datetime.datetime.utcnow()
        self.mini = (self.now - datetime.timedelta(days=1)).isoformat() + "Z"
        self.maxi = (self.now + datetime.timedelta(days=1)).isoformat() + "Z"
        self.start_rule = self.now.strftime("%Y-%m-%d")
        self.end_rule = (self.now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    def send_slack(self, start, message):
        msg = {
            "username": start,
            "text": message,
            "icon_emoji": "tada",
            "mrkdwn": True,
        }
        try:
            requests.post(
                self.slack_webhook,
                data=json.dumps(msg),
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            print(e)

    def parse_leaves(self, events):
        send_data_list = []
        for event in events:
            st_dateTime = event["start"].get("dateTime")
            st_date = event["start"].get("date")
            ed_date = event["end"].get("date")
            summary = event["summary"]
            end = None
            if st_dateTime:
                if (
                    datetime.datetime.strptime(
                        st_dateTime, "%Y-%m-%dT%H:%M:%S%z"
                    ).date()
                    >= self.now.date()
                ):
                    trans_st_dateTime = datetime.datetime.strptime(
                        st_dateTime, "%Y-%m-%dT%H:%M:%S%z"
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    send_data_list.append((trans_st_dateTime + " " + summary))
            elif st_date:
                end = datetime.datetime.strptime(
                    ed_date, "%Y-%m-%d"
                ) - datetime.timedelta(days=1)
                if (
                    self.now.date() <= end.date()
                    and self.now.date()
                    >= datetime.datetime.strptime(st_date, "%Y-%m-%d").date()
                ):
                    send_data_list.append(
                        (self.now.date().strftime("%Y-%m-%d") + " " + summary)
                    )
        print(send_data_list)
        send_data = ""
        for i in send_data_list:
            send_data += i
            send_data += "\n"

        return self.now.date().strftime("%Y-%m-%d") + " leave", send_data.strip()

    def main(self):
        print(self.now.date())
        """Shows basic usage of the Google Calendar API.
        Prints the start and name of the next 10 events on the user's calendar.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials, self.scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())

        try:
            service = build("calendar", "v3", credentials=creds)

            # Call the Calendar API
            events_result = (
                service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=self.mini,
                    maxResults=self.maxResults,
                    singleEvents=True,
                    timeMax=self.maxi,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No upcoming events found.")
                return
            else:
                title, contents = self.parse_leaves(events)
                # self.send_slack(title, contents)
                self.slack_utils.send_message_for_post(title, contents)

        except HttpError as error:
            print("An error occurred: %s" % error)


if __name__ == "__main__":
    aws_utils = AwsUtils()
    credentials = "credentials.json"
    token_file = "token.json"
    if not os.path.exists(credentials):
        with open(credentials, "w") as cred:
            cred.write(aws_utils.get_parameter("credentials"))
    if not os.path.exists(token_file):
        with open(token_file, "w") as cred:
            cred.write(aws_utils.get_parameter("token_file"))
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    roo_leave_calendar_id = aws_utils.get_parameter("roo_leave_id")
    calendar_id = "{}@group.calendar.google.com".format(roo_leave_calendar_id)
    maxResults = 100
    # slack_webhook_path = aws_utils.get_parameter("slack_webhook")
    # slack_webhook = "https://hooks.slack.com/services/{}".format(slack_webhook_path)
    # GoogleCalendar(scopes, calendar_id, maxResults, slack_webhook).main()
    dev_slack_token = aws_utils.get_parameter("dev_slack_token")
    slack_channel_name = aws_utils.get_parameter("slack_channel_name")
    slack_utils = SlackMessage(dev_slack_token, slack_channel_name)
    GoogleCalendar(scopes, calendar_id, maxResults, slack_utils).main()
