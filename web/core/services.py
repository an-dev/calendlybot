import slack


class SlackMessageService:
    def __init__(self, token):
        self.client = slack.WebClient(token=token)

    def send(self, channel, text, blocks=None, attachments=None):
        kwargs = {'channel': channel, 'text': text}
        if blocks:
            kwargs['blocks'] = blocks
        if attachments:
            kwargs['attachments'] = attachments
        return self.client.chat_postMessage(**kwargs)

    def update_interaction(self, response_url, text=None, blocks=None):
        kwargs = {"delete_original": True, "response_type": "in_channel"}
        if blocks:
            kwargs['blocks'] = blocks
        if text:
            kwargs['text'] = text
        return self.client.api_call(response_url, json=kwargs)
