def read_config():
    with open('config', 'rt') as file:
        lines = file.readlines()
        return {item.split('=')[0]: item.split('=')[1].strip() for item in lines if '=' in item}


def get_user_name(user):
    if user.username is not None:
        return user.username
    else:
        return user.first_name + \
               (f" {user.last_name}" if user.last_name is not None else '')
