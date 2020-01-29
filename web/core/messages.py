class SlackMarkdownEventCreatedMessage:
    def __init__(self, name, event_name, event_start_time, invitee_name, invitee_email, invitee_timezone):
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
    def __init__(self, name, event_name, event_start_time, invitee_name, invitee_email, canceler_name):
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


class SlackMarkdownUpgradeMessage:
    def __init__(self, workspace):
        self.workspace = workspace

    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"An event was created or cancelled on your calendar.\n"
                    f"Please upgrade to continue receiving detailed notifications.\n"
                    f"Thanks for giving calendlyBot a try!"
                }
            }
        ]
