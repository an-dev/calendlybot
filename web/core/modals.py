from web.core.actions import SELECT_HOOK_DEST_CHANNEL


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


class SlackDestinationErrorModal(SlackErrorModal):
    def get_title(self):
        return "Notification Error"

    def get_descr(self):
        return "Could not set event notification target. " \
               "Please try again or *<mailto:support@calenduck.co|contact support>*"


class SlackConnectModal:
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
                {
                    "type": "image",
                    "block_id": "image",
                    "image_url": "https://help.calendly.com/hc/article_attachments/360059408434/Screen_Shot_2020-03-04_at_9.23.54_AM.png",
                    "alt_text": "Calendly Instructions"
                },
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


class SlackDestinationChannelModal:
    def get_view(self):
        return {
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Select Channel"
            },
            "submit": {
                "type": "plain_text",
                "text": "Submit"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "block_channel",
                    "element": {
                        "type": "conversations_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a channel"
                        },
                        "filter": {
                            "include": [
                                "public",
                                "private"
                            ]
                        },
                        "action_id": "select_channel"
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Where should I send event notifications to?"
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
                            "text": "If you select a _private_ channel as destination, "
                                    "*remember to add Calenduck to that group*! (You can do this by typing "
                                    "`/invite @calenduck` in the specific group)"
                        }
                    ]
                }
            ]
        }
