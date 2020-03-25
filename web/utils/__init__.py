COMMAND_LIST = ['connect', 'upgrade', 'help']


def eligible_user(user):
    return user['is_bot'] is False and user['id'] != 'USLACKBOT'
