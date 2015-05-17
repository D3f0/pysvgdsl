from __future__ import print_function
from multiprocessing import Process, Queue
from twisted.web import static, server, resource
import os
import atexit


server_process = None


class RetryingConnectionSite(server.Site):
    def startFactory(self, *args):
        print("startFactory")
        server.Site.startFactory(self, *args)

    def stopFactory(self, *args):
        print("stopFactory")
        server.Site.stopFactory(self, *args)


def _webserver(port, outqueue):
    """Starts a webserver in port"""
    from twisted.internet import reactor

    import atexit

    atexit.register(print, "Server shutdown")
    root = resource.Resource()
    root.putChild("static", static.File(os.path.join(os.getcwd(), 'static')))
    reactor.listenTCP(port, RetryingConnectionSite(root))
    reactor.callLater(0, outqueue.put, port)
    reactor.run()


def start_webserver(inital_port=6543, wait_until_started=True):
    """Starts werbserver in another process.
    Waits until completed
    @param wait_until_started Blocks until webserver is started
    @return True if server is started, False if it's already started
    """
    global server_process
    if server_process.is_alive():
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
        queue.get()
    return True

def stop_server():
    """Stop webserver"""
    global server_process
    if not server_process:
        return
    # This functions seems to be inoffensive if the process has exited
    print("Killing server...")
    server_process.terminate()

atexit.register(stop_server)


def test():
    import requests
    port = 6543
    start_webserver(port, wait_until_started=True)
    response = requests.get('http://localhost:{port}/static/dynsvg.js'.format(
        port=port
    ))
    with open('./static/dynsvg.js') as fp:
        data = fp.read()

    assert data == response.content
