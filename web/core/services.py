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

    def update(self, channel, ts, text, blocks=()):
        kwargs = {'channel': channel, 'ts': ts, 'text': text, 'blocks': blocks}
        return self.client.chat_update(**kwargs)
