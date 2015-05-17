from __future__ import print_function
from multiprocessing import Process, Queue
from twisted.web import static, server, resource
from twisted.internet.error import CannotListenError
import os
import atexit


server_process = None


def _webserver(port, outqueue, maxtries=None):
    """Starts a webserver in port"""
    from twisted.internet import reactor
    if maxtries is None:
        maxtries = 20

    connected = False

    root = resource.Resource()
    root.putChild("static", static.File(os.path.join(os.getcwd(), 'static')))
    while maxtries and not connected:
        try:
            reactor.listenTCP(port, server.Site(root))
            connected = True

        except CannotListenError:
            maxtries -= 1
            port += 1

    reactor.callLater(0, outqueue.put, (connected, port))
    reactor.run()


def start_webserver(inital_port=6543, wait_until_started=True):
    """Starts werbserver in another process.
    Waits until completed
    @param wait_until_started Blocks until webserver is started
    @return (connected, port)
    """

    global server_process
    if server_process is not None and server_process.is_alive():
        return False
    queue = Queue(1)
    server_process = Process(
        target=_webserver,
        kwargs={
            'port': inital_port,
            'outqueue': queue
        }
    )
    server_process.start()
    if wait_until_started:
        connected, port = queue.get()
    atexit.register(stop_server)

    return connected, port


def stop_server():
    """Stop webserver"""
    global server_process
    if server_process is None:
        return
    # This functions seems to be inoffensive if the process has exited
    server_process.terminate()

atexit.register(stop_server)


def test():
    import requests
    port = 9090
    ok, port = start_webserver(port, wait_until_started=True)
    assert ok, "Error tyring to connect, last port tested %d" % port
    response = requests.get('http://localhost:{port}/static/dynsvg.js'.format(
        port=port
    ))
    with open('./static/dynsvg.js') as fp:
        data = fp.read()

    assert data == response.content
