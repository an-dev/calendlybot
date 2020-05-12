import logging

from django.templatetags.static import static

logger = logging.getLogger(__name__)


class SlackErrorModal:
    def get_view(self):
        return {
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": self.get_title(),
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self.get_descr()
                    }
                }
            ]
        }


class SlackDisconnectErrorModal(SlackErrorModal):
    def get_title(self):
        return "Disconnect Error"

    def get_descr(self):
        return "Could not disconnect Calendly account. " \
               "Please try again or *<mailto:support@calenduck.co|contact support>*"


class SlackConnectModal:
    def __init__(self, private_metadata=None):
        self.private_metadata = private_metadata

    def get_view(self):
        return {
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Connect to Calendly",
            },
            "submit": {
                "type": "plain_text",
                "text": "Connect",
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel",
            },
            "private_metadata": self.private_metadata,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*1.* Login into Calendly. At the top of any page, select 'Integrations'.\n"
                                "*2.* Select Copy Key.\n"
                                "*3.* Paste in the field down below"
                    }
                },
                # {
                #     "type": "image",
                #     "block_id": "image",
                #     "image_url": static('web/img/tutorial.png'),
                #     "alt_text": "Calendly Instructions"
                # },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "*Calenduck works only with Calendly Premium and Pro accounts. "
                                    "<https://help.calendly.com/hc/en-us/articles/223195488|Learn more>.*"
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
                    "type": "input",
                    "block_id": "block_connect",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "input_connect"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Add your API Key"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "We do not share your API Key with any third party and never will. "
                                    "For more information, see our <https://calenduck.co/privacy/|Privacy Policy>."
                        }
                    ]
                }
            ]
        }


class SlackConnectModalWithError:
    def __init__(self, block_id, error):
        self.block_id = block_id
        self.error = error

    def get_view(self):
        return {
            "response_action": "errors",
            "errors": {
                self.block_id: self.error
            },
        }
