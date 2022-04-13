def read_config():
    with open('config', 'rt') as file:
        lines = file.readlines()
        return {item.split('=')[0]: item.split('=')[1].strip() for item in lines if '=' in item}
