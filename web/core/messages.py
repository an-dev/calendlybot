from django.conf import settings


class SlackMarkdownEventCreatedMessage:
    def __init__(self, name, event_name, event_start_time, invitee_name, invitee_email,
                 invitee_timezone):
        self.name = name
        self.event_name = event_name
        self.event_start_time = event_start_time
        self.invitee_name = invitee_name
        self.invitee_email = invitee_email
        self.invitee_timezone = invitee_timezone

    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hi {self.name}, a new event has been *scheduled*."
                }
            }
        ]

    def get_attachments(self):
        return [{
            "color": "#2EB67D",
            "blocks": [
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Event Type:*\n{self.event_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Invitee:*\n{self.invitee_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Event Date/Time:*\n{self.event_start_time}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Invitee Email:*\n<mailto:{self.invitee_email}|{self.invitee_email}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*<https://calendly.com/app/scheduled_events/user/me|View invitee in Calendly>*"
                        }
                    ]
                }
            ]
        }]


class SlackMarkdownEventCanceledMessage:
    def __init__(self, name, event_name, event_start_time, invitee_name, invitee_email,
                 canceler_name):
        self.name = name
        self.event_name = event_name
        self.event_start_time = event_start_time
        self.invitee_name = invitee_name
        self.invitee_email = invitee_email
        self.canceler_name = canceler_name

    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hi {self.name}, the event below has been *canceled*."
                }
            }
        ]

    def get_attachments(self):
        return [{
            "color": "#E01E5A",
            "blocks": [{
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Event Type:*\n{self.event_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Invitee:*\n{self.invitee_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Event Date/Time:*\n{self.event_start_time}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Invitee Email:*\n<mailto:{self.invitee_email}|{self.invitee_email}>"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Canceled by:*\n{self.canceler_name}"
                    },

                ]
            }]
        }]


class SlackMarkdownUpgradePromptMessage:
    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"An event was created or cancelled on your calendar.\n"
                            f"Please type `/duck upgrade` to continue receiving detailed notifications."
                }
            }
        ]


class SlackMarkdownUpgradeLinkMessage:
    def __init__(self, session_id):
        self.session_id = session_id

    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<{settings.SITE_URL}/subscribe/{self.session_id}/|Click here>* to upgrade your plan.\n"
                            "Thanks for giving Calenduck a try!"
                }
            }
        ]


class SlackMarkdownHelpMessage:
    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Here are some useful tips!"
                }
            }
        ]

    def get_attachments(self):
        return [{
            "color": "#36C5F0",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "• `/duck connect`: Connect your Slack account to Calendly\n• `/duck upgrade`: Upgrade to a new plan based on your workspace size"
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Still need some help? *<mailto:andy.idiaghe@gmail.com|Contact us>*"
                        }
                    ]
                }
            ]
        }]
