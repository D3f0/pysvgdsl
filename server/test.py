from . import start_webserver
import requests


def test():
    port = 9090
    ok, port = start_webserver(port, wait_until_started=True, log_file='./logs.txt')
    assert ok, "Error tyring to connect, last port tested %d" % port
    response = requests.get('http://localhost:{port}/static/dynsvg.js'.format(
        port=port
    ))
    with open('./static/dynsvg.js') as fp:
        data = fp.read()

    assert data == response.content
