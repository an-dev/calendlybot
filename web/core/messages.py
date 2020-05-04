from django.conf import settings

from web.core.actions import *

STATIC_START_MSG = 'Type `/duck connect your-calendly-token` to start!'
STATIC_HELP_MSG = 'Please try again or type `/duck help`.'
STATIC_FREE_ACCT_MSG = "Calenduck works only with Calendly Premium and Pro accounts. " \
                       "<https://help.calendly.com/hc/en-us/articles/223195488|Learn more>."

SCHEDULED_MSG_COLOR = '#2EB67D'
CANCELLED_MSG_COLOR = '#E01E5A'
INFO_MSG_COLOR = '#36C5F0'


class SlackMarkdownEventCreatedMessage:
    def __init__(self, name, event_name, event_start_time, invitee_name, invitee_email,
                 invitee_timezone, location=None):
        self.name = name
        self.event_name = event_name
        self.event_start_time = event_start_time
        self.invitee_name = invitee_name
        self.invitee_email = invitee_email
        self.invitee_timezone = invitee_timezone
        self.location = location

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
            "color": SCHEDULED_MSG_COLOR,
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
                            "text": f"*Location:*\n{self.location if self.location else 'N/A'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "\n\n*<https://calendly.com/app/scheduled_events/user/me|View invitee on Calendly>*"
                        }
                    ]
                }
            ]
        }]


class SlackMarkdownEventCancelledMessage:
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
            "color": CANCELLED_MSG_COLOR,
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
                    "text": f"*<{settings.SITE_URL}/subscribe/{self.session_id}/|Click here>* to upgrade your plan. "
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
            "color": INFO_MSG_COLOR,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "• `/duck connect your-calendly-token`: Connect your Slack account to Calendly\n"
                                "• `/duck disconnect`: Disconnect your Slack account from Calendly\n"
                                "• `/duck upgrade`: Upgrade to a new plan based on your workspace size\n"
                                "• `/duck help`: See this message\n"
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
                            "text": "Don't know how to get your calendly token? "
                                    "*<https://developer.calendly.com/v1/docs/getting-your-authentication-token|Click here>*\n"
                                    "Have a free account? Calenduck works only with *<https://help.calendly.com/hc/en-us/articles/223195488|Premium and Pro>* accounts\n"
                                    "Still need some help? *<mailto:support@calenduck.co|Contact us>*"
                        },
                    ]
                }
            ]
        }]


class SlackMarkdownNotificationDestinationMessage:

    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Where do you want me to send event notifications?"
                }
            }
        ]

    def get_attachments(self):
        return [{
            "color": INFO_MSG_COLOR,
            "blocks": [{
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Send to me"
                        },
                        "action_id": BTN_HOOK_DEST_SELF
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Send to channel"
                        },
                        "action_id": BTN_HOOK_DEST_CHANNEL
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Maybe later"
                        },
                        "action_id": BTN_CANCEL
                    }
                ]
            }]
        }]


class SlackMarkdownNotificationDestinationChannelMessage:

    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Where should I send notifications to?"
                },
                "accessory": {
                    "type": "conversations_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select channel",
                    },
                    "filter": {
                        "include": [
                            "public",
                            "private"
                        ],
                    },
                    "action_id": SELECT_HOOK_DEST_CHANNEL
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Not sure yet? No worries."
                },
                "accessory": {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Maybe later",
                    },
                    "action_id": BTN_CANCEL
                }
            }
        ]


class SlackHomeViewMessage:

    def __init__(self, slack_user):
        self.slack_user = slack_user

    def get_connect_button(self):
        if self.slack_user.calendly_authtoken:
            return {
                "type": "button",
                "style": "danger",
                "text": {
                    "type": "plain_text",
                    "text": "Disconnect"
                },
                "action_id": BTN_DISCONNECT
            }
        else:
            return {
                "type": "button",
                "style": "primary",
                "text": {
                    "type": "plain_text",
                    "text": "Connect"
                },
                "action_id": BTN_CONNECT
            }

    def get_masked_token(self):
        if self.slack_user.calendly_authtoken:
            return f"{'*' * 24}{self.slack_user.calendly_authtoken[-8:]}"
        return 'Use the button below to connect your Calendly account'

    def get_email(self):
        if self.slack_user.calendly_email:
            return f'{self.slack_user.calendly_email} (<https://calendly.com/event_types/user/me|Go to Calendly account>)'
        return 'Use the button below to connect your Calendly account'

    def get_current_configuration(self):
        webhook = self.slack_user.webhooks.first()
        if webhook:
            workspace = self.slack_user.workspace
            destination = f"<slack://user?team={workspace.slack_id}&id={webhook.destination_id}|*you*>"
            if not webhook.destination_id.startswith('U'):
                destination = \
                    f"<slack://channel?team={workspace.slack_id}&id={webhook.destination_id}|*channel*>"
            return f"Sending *all events* notifications to {destination}"
        return "You haven't setup any notification preferences."

    def get_view(self):
        return {
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Calenduck*"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "text": "Hello Andy! Here's what you can do Calenduck:",
                            "type": "mrkdwn"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Help"
                            }
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Feedback"
                            }
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                            "alt_text": "placeholder"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Calendly account*"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Email*: {self.get_email()}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Token*: {self.get_masked_token()}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [self.get_connect_button()]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                            "alt_text": "placeholder"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Current configuration*\n"
                                    "Your configuration is determined by your notification preferences below"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self.get_current_configuration()
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                            "alt_text": "placeholder"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Notifications preferences*"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Where should I send event notifications?*"
                    },
                    "accessory": {
                        "type": "overflow",
                        "action_id": CHOICE_DEST,
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Send to me"
                                },
                                "value": BTN_HOOK_DEST_SELF
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Send to channel"
                                },
                                "value": BTN_HOOK_DEST_CHANNEL
                            }
                        ]
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Which events should Calenduck notify you about?*"
                    },
                    "accessory": {
                        "type": "multi_static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select items",
                        },
                        "options": [
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Choice 1",
                                },
                                "value": "value-0"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Choice 2",
                                },
                                "value": "value-1"
                            },
                            {
                                "text": {
                                    "type": "plain_text",
                                    "text": "Choice 3",
                                },
                                "value": "value-2"
                            }
                        ]
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                            "alt_text": "placeholder"
                        }
                    ]
                }
            ]
        }
