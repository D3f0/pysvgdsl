import os
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File
from twisted.web.resource import Resource
from autobahn.twisted.resource import WebSocketResource
from twisted.python import log
import time

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol, \
    listenWS


class ListenAwareSite(Site):
    pass


class SVGBroadcastProtocol(WebSocketServerProtocol):
    def __init__(self, *args, **kwargs):
        log.msg(str(args) + str(kwargs))
        super(SVGBroadcastProtocol, self).__init__(*args, **kwargs)

    def onOpen(self):
        log.msg("Connection from %s" % self)
        self.factory.register(self)

    def _onMessage(self, payload, isBinary):
        if not isBinary:
            msg = "{} from {}".format(payload.decode('utf8'), self.peer)
            self.factory.broadcast(msg)

    def connectionLost(self, reason):
        log.msg("Websocket closed %s %s" % (self, reason))
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)




class SVGBroadcastFactory(WebSocketServerFactory):

    """
    WebSocket server factory with cookie/sessions map.
    """

    protocol = SVGBroadcastProtocol

    def __init__(self, url, logger=None):
        # Connect to ZMQ
        WebSocketServerFactory.__init__(self, url, debug=False)
        # map of cookies
        self._cookies = {}
        self.clients = []
        self.logger = logger

    def buildProtocol(self, *args):
        return WebSocketServerFactory.buildProtocol(self, *args)

    def register(self, client):
        if client not in self.clients:
            log.msg("registered client {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            log.msg("unregistered client {}".format(client.peer))
            self.clients.remove(client)

    def broadcast(self, msg):
        log.msg("broadcasting message '{}' ..".format(msg))
        for c in self.clients:
            c.sendMessage(msg.encode('utf8'))
            print("message sent to {}".format(c.peer))


class PusherResource(Resource):
    """
    POST -> broadcast to websockets
    """

    def __init__(self, ws_resource=None):
        Resource.__init__(self)
        self.ws_resource = ws_resource

    def render_POST(self, request):
        headers = request.getAllHeaders()

        content_type = headers.get('content-type', None)

        if content_type != 'application/json':
            headers.setResponseCode(400)
            resp = ("Missing content type or different from application/json. "
                    "Got %s instead\n") % (content_type, )
            return resp

        data = request.content.read()
        self.ws_resource.broadcast(data)
        log.msg(
            "Forwarded %s to %d websockets" % (
                data[:30],
                len(self.ws_resource.clients)
            )
        )
        return "OK!"


class RootResource(Resource):
    def __init__(self, *args):
        Resource.__init__(self, *args)
        self.startup_time = time.time()

    def render(self, request):
        pid = os.getpid()
        uptime = time.time() - self.startup_time
        return """
        IPython SVG Bridget
        pid = {pid}
        uptime = {uptime}
        """.format(**locals())


class APIResource(Resource):
    def __init__(self, ws_server):
        self.ws_server = ws_server


def build_site(port, ws_path='ws', logger=None):
    """Creates a site instance"""
    static_path = os.path.join(os.getcwd(), 'static')
    # FIXME: Put something interesting here
    root = RootResource()
    root.putChild("static", File(static_path))
    factory = SVGBroadcastFactory(
        "ws://localhost:{port}/{ws_path}".format(**locals())
    )
    ws = WebSocketResource(factory)
    root.putChild(ws_path, ws)
    root.putChild('pusher', PusherResource(factory))
    root.putChild('/api', APIResource(ws))
    site = Site(root)
    return site
