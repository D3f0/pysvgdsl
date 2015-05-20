/**
 * Mantains a RPC connection a webserver
 */
define(['d3'], function (d3) {
    var connected = false;
    var wsurl = null;
    var connection = null;
    var node = null;

    function onMessage (msg) {
        var data = null;
        try {
            data = JSON.parse(msg.data)
        } catch (e) {
            console.error("Parsing JSON message from", msg.data, e);
        }
        console.log("Message receied");
        console.info(msg);
        //debugger;
    }
    function onError(err) {
        console.error("WS error", error);
    }
    function onOpen() {
        console.log("Connected WS to "+wsurl+" working on "+node);
    }

    return {
         makeConnection: function (url, svg_node_id) {
            console.info(d3);
            var node = d3.select('#'+svg_node_id);
            wsurl = url;
            connection = new WebSocket(url);
            connection.onopen = onOpen;
            connection.onmessage = onMessage;
            connection.onerror = onError;
        }
    }
});
