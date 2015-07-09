from os.path import join, dirname

from json import loads

from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line
from tornado.web import RequestHandler, Application
from tornado.websocket import WebSocketHandler


clients = []


# noinspection PyAbstractClass
class SocketHandler(WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in clients:
            clients.append(self)

    def on_close(self):
        if self in clients:
            clients.remove(self)


class MainHandler(RequestHandler):
    def get(self):
        self.render(u"index.html")


class ApiHandler(RequestHandler):
    value = 5

    def post(self, *args, **kwargs):
        try:
            data = loads(self.request.body)
            if u"val" not in data:
                self.send_error(400, reason=u"Parameter `val` required")
                return
            
            new_val = int(data[u"val"])
            if not -1 < new_val < 10:
                self.send_error(406, reason=u"Parameter `val` should be in range [0..9]")
                return
                
            ApiHandler.value = new_val
        except StandardError:
            self.send_error(406, reason=u"Please send following JSON: `val`")
            return

        for cl in clients:
            cl.write_message({u"val": ApiHandler.value})
            
        self.finish({u"success": True})

    def get(self, *args, **kwargs):
        self.finish({u"val": ApiHandler.value})


def _main():
    define(u"port", default=9090, help=u"run on the given port", type=int)
    define(u"debug", default=True, help=u"run in debug mode")
    parse_command_line()
    print("Starting on port {}".format(options.port))

    app = Application(
        [
            (r"/", MainHandler),
            (r'/ws', SocketHandler),
            (r'/api', ApiHandler),
        ],
        template_path=join(dirname(__file__), u"templates"),
        debug=options.debug,
    )
    app.listen(options.port)
    IOLoop.current().start()

if __name__ == u"__main__":
    _main()
