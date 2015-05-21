/**
 * Mantains a RPC connection a webserver
 */
define(['d3'], function (d3) {
    var connected = false;
    var wsurl = null;
    var connection = null;
    var node = null;

    /**
     * [getObjectsById description]
     * @param  {Object} data An object wich keys are ID's in an SVG file
     *
     * This functions should work with different kind of messages.
     * Fore example those processed in
     * https://github.com/D3f0/txscada/blob/master/src/pysmve/nguru/apps/hmi/static/hmi/js/realtime_watch.js
     */
    function getObjectsById(msg) {
        var data = JSON.parse(msg.data)
        return data;
    }

    /** Apply changes to nodes
     *  node {Object} d3 selection of node
     *  updates {Object} Stores updates
     */
    function applyChanges(node, updates) {
        // Call itself recureisvely if the target element is a group
        if (node.node().tagName == "g") {
            node.selectAll('path, rect').each(function () {
                applyChanges(d3.select(this), updates);
            });

        } else {
            console.info("Applying "+updates+" to "+node);
            _.each(updates, function (value, attribute) {
                if (node.attr('tag') == 'nopaint') {
                    console.info("Skipping");
                    return;
                }
                if (attribute == 'text') {
                    node.text(value);
                } else {
                    node.style(attribute, value);
                }

            });
        }
    }

    /**
     * Event handler for messages send from the server through ws
     * @param  {MessageEvent} msg Attribtue `data` hold the message payload
     */
    function onMessage (msg) {
        var data = null;
        try {
            data = getObjectsById(msg);
        } catch (e) {
            console.error("Parsing JSON message from", msg.data, e);
        }
        console.log("Message receied");
        console.info(data);

        _.each(data, function (updates, node_id) {
            var selector = '#'+node_id;
            var localNode = node.select(selector);
            if (!localNode.empty()) {
                console.info("Updating element ", localNode);
                applyChanges(localNode, updates)
            } else {
                // debugger;
                console.error(selector+" did not match with any element in "+node);
            }
        });
        //debugger;
    }
    function onError(err) {
        console.error("WS error", error);
    }
    function onOpen() {
        console.log("Connected WS to "+wsurl+" working on "+node);
    }

    return {
        /**
         * Creates a connection
         * @param  {string} url         websocket url to receive updates
         * @param  {string} svg_node_id ID for the svg node to work on
         * @return {undefined}           This function does not return anything useful
         */
         makeConnection: function (url, svg_node_id) {
            console.info(d3);
            node = d3.select(svg_node_id);
            wsurl = url;
            connection = new WebSocket(url);
            connection.onopen = onOpen;
            connection.onmessage = onMessage;
            connection.onerror = onError;
        }
    }
});
