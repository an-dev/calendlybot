import logging
from calendly import Calendly

from web.utils import user_eligible

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


class SlackDestinationErrorModal(SlackErrorModal):
    def get_title(self):
        return "Notification Error"

    def get_descr(self):
        return "Could not set event notification target. " \
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
    def __init__(self, user, private_metadata=None):
        self.user = user
        self.private_metadata = private_metadata

    def get_event_destinations(self):
        if self.user.webhooks:

            initial_option = None
            destination_name = 'Could not retrieve event name'

            import slack
            client = slack.WebClient(token=self.user.workspace.bot_token)
            # get users
            users = [{'id': u['id'], 'name': u['profile'].get('first_name', u['profile']['real_name'])} for u in
                     client.users_list().data['members'] if user_eligible(u)]
            user_list = [{'text': {'type': 'plain_text', 'text': u['name']}, 'value': u['id']} for u in users]
            # get channels
            channels = [{'id': c['id'], 'name': c['name']} for c in client.channels_list().data['channels']]
            channel_list = [{'text': {'type': 'plain_text', 'text': c['name']}, 'value': c['id']} for c in channels]
            # get private channels
            groups = [{'id': g['id'], 'name': g['name']} for g in client.groups_list().data['groups']]
            group_list = [{'text': {'type': 'plain_text', 'text': g['name']}, 'value': g['id']} for g in groups]

            for hook in self.user.webhooks.all():
                section = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "",
                    },
                    "accessory": {
                        "type": "static_select",
                        "action_id": f"hook_{hook.event_id}",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select destination"
                        },
                        "option_groups": [
                            {
                                "label": {
                                    "type": "plain_text",
                                    "text": "Users"
                                },
                                "options": user_list
                            },
                            {
                                "label": {
                                    "type": "plain_text",
                                    "text": "Channels"
                                },
                                "options": channel_list
                            },
                            {
                                "label": {
                                    "type": "plain_text",
                                    "text": "Private Channels"
                                },
                                "options": group_list
                            }
                        ]
                    },
                }

                if hook.destination_id:
                    destination_id = hook.destination_id
                    destination_obj = None
                    if destination_id.startswith('U'):
                        destination_obj = \
                        [a for a in filter(lambda x: x['name'] if x['id'] == destination_id else None, users)][0]

                    if destination_id.startswith('C'):
                        destination_obj = \
                            [a for a in filter(lambda x: x['name'] if x['id'] == destination_id else None, channels)][0]

                    if destination_id.startswith('G'):
                        destination_obj = \
                            [a for a in filter(lambda x: x['name'] if x['id'] == destination_id else None, groups)][0]

                    if destination_obj:
                        initial_option = {
                            'text': {'type': 'plain_text', 'text': destination_obj['name']}, 'value': destination_id}
                    else:
                        logger.warning(f'Could not load initial option for {destination_id} for {hook}')

                    try:
                        calendly = Calendly(self.user.calendly_authtoken)
                        destination_name = [a['attributes']['name'] for a in
                                            filter(lambda x: x['id'] == hook.event_id,
                                                   calendly.event_types()['data'])][0]
                    except Exception:
                        logger.exception(f'{destination_name}')

                section['text']['text'] = destination_name

                if initial_option:
                    section['accessory']['initial_option'] = initial_option
                yield section
        else:
            yield {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "Select at least 1 event first."
                    }
                ]
            }

    def get_view(self):
        gen = self.get_event_destinations()

        return {
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Select Destinations"
            },
            "submit": {
                "type": "plain_text",
                "text": "Done"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "private_metadata": self.private_metadata,
            "blocks": [d for d in gen]
        }
