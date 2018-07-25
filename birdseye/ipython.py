import inspect
import socket
import sys
from io import BytesIO, StringIO
from threading import currentThread, Thread

from IPython.core.display import HTML, display
from werkzeug.local import LocalProxy
from werkzeug.serving import ThreadingMixIn

from birdseye import eye, PY2
from birdseye.server import app

fake_stream = BytesIO if PY2 else StringIO

thread_proxies = {}


def stream_proxy(original):
    def p():
        frame = inspect.currentframe()
        while frame:
            if frame.f_code == ThreadingMixIn.process_request_thread.__code__:
                return fake_stream()
            frame = frame.f_back
        return thread_proxies.get(currentThread().ident,
                                  original)

    return LocalProxy(p)


sys.stderr = stream_proxy(sys.stderr)
sys.stdout = stream_proxy(sys.stdout)


def run_server():
    thread_proxies[currentThread().ident] = fake_stream()
    try:
        app.run(
            debug=True,
            port=7777,
            host='127.0.0.1',
            use_reloader=False,
        )
    except socket.error:
        pass


def cell_magic(_line, cell):
    Thread(target=run_server).start()
    call_id = eye.exec_ipython_cell(cell)
    html = HTML('<iframe '
                '    src="http://localhost:7777/ipython_call/%s"' % call_id +
                '    style="width: 100%"'
                '    height="500"'
                '/>')
    # noinspection PyTypeChecker
    display(html)