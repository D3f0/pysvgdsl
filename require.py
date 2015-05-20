from flask import Flask
from server.control import start_webserver
from jinja2 import Template

app = Flask(__name__)

ok, port = start_webserver()


@app.route('/')
def index():
    #template = loader.get_template('test_require.html')
    #output = template.render(port=port)

    template = Template('''
    <html>
        <head>
        <script src="/static/require.js"></script>
        </head>
        <body>
        <script>
        require.config({
            paths: {
                'd3': '/static/d3'
            },
            urlArgs: "bust=" + (new Date()).getTime()
        });
        require(['d3'], function (d3) {
            debugger;
        });
        </script>

        </body>
    </html>
    ''')
    output = template.render(port=port)
    return output

app.run(debug=True)
