from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackMessage:
    def __init__(self, token, channel):
        self.client = WebClient(token=token)
        self.channel = channel

    def send_message_for_post(self, start, message):
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": start,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "plain_text", "text": message},
                    ],
                },
            ]

            response = self.client.chat_postMessage(
                channel=self.channel, text=start, blocks=blocks
            )
        except SlackApiError as e:
            print(e)
