import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config

from slack_utils import SlackMessage


class GoogleCalendar:
    def __init__(self, scopes, calendar_id, maxResults, slack_utils, cred):
        self.service = self.__init_service(cred)
        self.scopes = scopes
        self.calendar_id = calendar_id
        self.maxResults = maxResults
        self.slack_utils = slack_utils
        self.now = datetime.datetime.utcnow()
        self.mini = (self.now - datetime.timedelta(days=1)).isoformat() + "Z"
        self.maxi = (self.now + datetime.timedelta(days=1)).isoformat() + "Z"
        self.start_rule = self.now.strftime("%Y-%m-%d")
        self.end_rule = (self.now + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    def __init_service(self, cred):
        creds = service_account.Credentials.from_service_account_info(cred)

        return build("calendar", "v3", credentials=creds)

    def parse_leaves(self, events):
        send_data_list = []
        for event in events:
            st_dateTime = event["start"].get("dateTime")
            end_dateTime = event["end"].get("dateTime")
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
                    trans_end_dateTime = datetime.datetime.strptime(
                        end_dateTime, "%Y-%m-%dT%H:%M:%S%z"
                    ).strftime("%H:%M:%S")
                    send_data_list.append(
                        (trans_st_dateTime + "-" + trans_end_dateTime + " " + summary)
                    )
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
        try:
            events_result = (
                self.service.events()
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
                if not contents:
                    return
                self.slack_utils.send_message_for_post(title, contents)

        except HttpError as error:
            print("An error occurred: %s" % error)


def lambda_handler(event, context):
    slack_utils = SlackMessage(config.DEV_SLACK_TOKEN, config.SLACK_CHANNEL_NAME)
    GoogleCalendar(
        config.SCPOES,
        config.CALENDAR_ID,
        config.MAXRESULTS,
        slack_utils,
        config.MACROPUS_WEB_DEV_CRED,
    ).main()
