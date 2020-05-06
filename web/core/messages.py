from calendly import Calendly
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
                        "text": "• `/duck`: View and manage your Calenduck settings\n"
                                "• `/duck upgrade`: Upgrade to a new plan based on your workspace size and usage\n"
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

class SlackHomeMessage:
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

    def get_space_template(self):
        return {
            "type": "context",
            "elements": [
                {
                    "type": "image",
                    "image_url": "https://api.slack.com/img/blocks/bkb_template_images/placeholder.png",
                    "alt_text": "placeholder"
                }
            ]
        }

    def get_divider_template(self):
        return {
            "type": "divider"
        }

    def get_calendly_template_head(self):
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "*Calendly account*"
                }
            ]
        }

    def get_calendly_template_email(self):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Email*: {self.get_email()}"
            }
        }

    def get_calendly_template_token(self):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Token*: {self.get_masked_token()}"
            }
        }

    def get_calendly_template_btn(self):
        return {
            "type": "actions",
            "elements": [self.get_connect_button()]
        }

    def get_conf_template_head(self):
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "*Current configuration*\n"
                            "Your configuration is determined by your notification preferences below"
                }
            ]
        }

    def get_conf_template_value(self):
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": self.get_current_configuration()
            }
        }

    def get_notification_template_head(self):
        return {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "*Notifications preferences*"
                }
            ]
        }

    def get_notification_template_choice(self):
        return {
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
        }

    def get_event_filters_template(self):

        try:
            calendly = Calendly(self.slack_user.calendly_authtoken)
            events = calendly.event_types()
            active_events = [{'id': e['id'], 'name': e['attributes']['name']} for e in events['data'] if
                             e['attributes']['active']]
            options = [{'text': {'type': 'plain_text', 'text': e['name']}, 'value': e['id']} for e in active_events]
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f'Could not retrieve events for api_key {self.slack_user.calendly_authtoken}')
            options = [{
                        "text": {
                            "type": "plain_text",
                            "text": "Could not retrieve events. Make sure your account is connected!"
                        },
                        "value": "None"
                    }]

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Which events should I notify you about?*"
            },
            "accessory": {
                "type": "multi_static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select events",
                },
                'action_id': EVENT_SELECT,
                "options": options
            }
        }

    def get_blocks(self):
        return [
            {
                "type": "section",
                "text": {
                    "text": f"Hello {self.slack_user.slack_name}!\nManage Calenduck's settings and notification preferences below",
                    "type": "mrkdwn"
                }
            },
            self.get_space_template(),
            self.get_calendly_template_head(),
            self.get_divider_template(),
            self.get_calendly_template_email(),
            self.get_calendly_template_token(),
            self.get_calendly_template_btn(),
            self.get_space_template(),
            self.get_conf_template_head(),
            self.get_divider_template(),
            self.get_conf_template_value(),
            self.get_notification_template_head(),
            self.get_divider_template(),
            self.get_event_filters_template(),
            self.get_notification_template_choice(),
            self.get_space_template()
        ]


class SlackHomeViewMessage(SlackHomeMessage):
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
                            "text": f"Hello {self.slack_user.slack_name}! Here's what you can do with Calenduck",
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
                self.get_space_template(),
                self.get_calendly_template_head(),
                self.get_divider_template(),
                self.get_calendly_template_email(),
                self.get_calendly_template_token(),
                self.get_calendly_template_btn(),
                self.get_space_template(),
                self.get_conf_template_head(),
                self.get_divider_template(),
                self.get_conf_template_value(),
                self.get_space_template(),
                self.get_notification_template_head(),
                self.get_divider_template(),
                self.get_event_filters_template(),
                self.get_notification_template_choice(),
                self.get_space_template()
            ]
        }
