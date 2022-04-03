import requests


def get_capitals():
    result = requests.get('https://ru.wikipedia.org/wiki/Список_столиц_государств').text
    tables = [piece.split('</table>')[0]
              for piece in result.split('<tbody>')
              if '</tbody>' in piece]

    rows = [[piece.split('</tr>') for piece in table.split('<tr>') if '</tr>' in piece] for table in tables]
    rows = map(lambda x: x[1:], rows)

    capitals = list()
    for table in rows:
        for row in table:
            temp_row = [piece.split('</td>')[0] for piece in row[0].split('<td>') if '</td>' in piece][1:]
            pack = list()
            for item in temp_row:
                a = list(filter(lambda x: x not in ['', '\n'],
                                [piece.split('>')[-1] for piece in item.split('</') if '>' in piece]))[0]
                pack.append(a)
            capitals.append(pack)
    capitals = capitals[:-1]
    return capitals

