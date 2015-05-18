from __future__ import print_function
from multiprocessing import Process, Queue
from twisted.internet.error import CannotListenError
import atexit

# Global var, only one instance of webserver per process.
server_process = None
server_process_port = None


def _webserver(port, outqueue, maxtries=None, log_file='server.log'):
    """
    Starts a webserver in port trying to bind to a port and retrying on
    different one if it does not succeed. This funcion is called in a subporcess
    and receives a multirpcess.Queue as outqueue to singal back server start
    """
    from twisted.internet import reactor
    from resources import build_site
    from twisted.python import log

    log.startLogging(open(log_file, 'w'))

    if maxtries is None:
        maxtries = 20

    connected = False

    while maxtries and not connected:
        try:
            # We need to pass the port so the application
            site = build_site(port)
            reactor.listenTCP(port, site)
            connected = True

        except CannotListenError:
            maxtries -= 1
            port += 1

    # As soon as the reactor starts processing events, singal the starter process
    # which port could be allocated
    reactor.callLater(0, outqueue.put, (connected, port))
    reactor.run()


def start_webserver(inital_port=6543, wait_until_started=True, block=False):
    """Starts werbserver in another process.
    It'll hook server termination at process exit. Useful to release resources
    when a IPython kernel is terminated.
    @param wait_until_started Blocks until webserver is started
    @return (connected, port)
    """
    global server_process, server_process_port
    if server_process is not None and server_process.is_alive():
        return True, server_process_port

    queue = Queue(1)
    server_process = Process(
        target=_webserver,
        kwargs={
            'port': inital_port,
            'outqueue': queue,
        }
    )
    server_process.start()
    if wait_until_started:
        try:
            connected, server_process_port = queue.get(timeout=1)
        except Exception as e:
            return False, None
    atexit.register(stop_server)
    if block:
        server_process.join()

    return connected, server_process_port


def stop_server():
    """Stop webserver"""
    global server_process
    if server_process is None:
        return
    # This functions seems to be inoffensive if the process has exited
    server_process.terminate()
