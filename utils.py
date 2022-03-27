def read_config():
    with open('config', 'rt') as file:
        lines = file.readlines()
        return {item.split('=')[0]: item.split('=')[1] for item in lines if '=' in item}
