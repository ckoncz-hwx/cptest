import cherrypy
import sys
import time

import logging
import logging.config

LOG = logging.getLogger('arcweb')

LOG_CONF = {
    'version': 1,
    'formatters': {
        'void': {'format': ''},
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(threadName)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'cherrypy_console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'void',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {'handlers': ['default'], 'level': 'INFO'},
        'arcweb': {'level': 'INFO'},
        'cherrypy.access': {
            'level': 'INFO',
            'handlers': ['cherrypy_console'],
            'propagate': False,
        },
        'cherrypy.error': {
            'level': 'INFO',
            'handlers': ['cherrypy_console'],
            'propagate': False,
        },
    },
}

connection_processing_sleep_time = 0
server_port = 8080
request_queue_size = 5


def patch_cp():
    # try to patch CherryPy's threadpool to provide logging
    import cheroot.workers.threadpool
    from cheroot.workers.threadpool import ThreadPool, queue, collections

    import logging

    LOG = logging.getLogger('arcweb')

    class ThreadPool2(ThreadPool):
        def __init__(
            self,
            server,
            min=10,
            max=-1,
            accepted_queue_size=-1,
            accepted_queue_timeout=10,
        ):
            self.server = server
            self.min = min
            self.max = max
            self._threads = []
            self._queue = queue.Queue(maxsize=accepted_queue_size)
            self._queue_put_timeout = accepted_queue_timeout
            # self.get = self._queue.get
            self._pending_shutdowns = collections.deque()
            LOG.info('ThreadPool2 created')

        def get(self, **args):
            result = self._queue.get(**args)
            LOG.info('queue.get, length %s', self._queue.qsize())
            return result

        def put(self, obj):
            self._queue.put(obj, block=True, timeout=self._queue_put_timeout)
            LOG.info('queue.put, length %s', self._queue.qsize())
            if connection_processing_sleep_time > 0:
                LOG.info(
                    f'slowing down connection processing by sleeping {connection_processing_sleep_time} seconds'
                )
                time.sleep(connection_processing_sleep_time)

    cheroot.workers.threadpool.ThreadPool = ThreadPool2


patch_cp()


def wsgi_app(environ, start_response):
    path = environ.get('PATH_INFO', '')

    sleep = 0
    path_elements = path.split('/')

    if 'sleep' in path_elements:
        sleep_index = path_elements.index('sleep')

        if sleep_index < len(path_elements) + 2:
            sleep = path_elements[sleep_index + 1]

    LOG.info(f'[{path}] about to sleep {sleep} seconds')
    time.sleep(float(sleep))
    LOG.info('sleeping done')

    status = "200 OK"  # HTTP Status
    headers = [("Content-type", "text/plain; charset=utf-8")]  # HTTP Headers
    start_response(status, headers)

    return [f'[{path}] slept {sleep} seconds.'.encode('utf-8')]


def start_server(options):

    LOG.info('server listening on %s:%s', options['host'], int(options['port']))

    from cheroot.wsgi import Server

    SERVER = Server(
        (options['host'], int(options['port'])),
        wsgi_app,
        numthreads=int(options['minthreads']),
        max=int(options['maxthreads']),
        server_name=options['server_name'],
        shutdown_timeout=int(options['shutdown_timeout']),
        request_queue_size=int(options['request_queue_size']),
    )
    try:
        SERVER.start()
    except KeyboardInterrupt:
        SERVER.stop()


def process_cli():
    """
    In some environments we might not have click, so do option parsing here
    """
    global connection_processing_sleep_time
    global server_port
    global request_queue_size

    usage = """
    Usage: cpserver.py [OPTIONS]

    Options:
        --connection_processing_sleep_time FLOAT
            sleep time (seconds) for connection processing
            Default is 0.0 (no sleep)

        --server_port INT
            server port (default is 8080)

        --request_queue_size INT
            request_queue_size (default is 5)

        --help                          Show this message and exit.
    """
    if '--help' in sys.argv:
        print(usage)
        sys.exit(0)

    connection_processing_sleep_time = getFloatOpt(
        connection_processing_sleep_time=connection_processing_sleep_time
    )
    server_port = getIntOpt(server_port=server_port)
    request_queue_size = getIntOpt(request_queue_size=request_queue_size)


def getIntOpt(**kwargs):
    """
    Only handles a single keyword arg
    """
    for k, v in kwargs.items():
        opt_value = getOpt(k)
        if opt_value == None:
            # no option found, return default:
            return v
        else:
            return int(opt_value)


def getFloatOpt(**kwargs):
    for k, v in kwargs.items():
        opt_value = getOpt(k)
        if opt_value == None:
            # no option found, return default:
            return v
        else:
            return float(opt_value)


def getOpt(key):
    opt_key = '--' + key
    if opt_key in sys.argv:
        index = sys.argv.index(opt_key)
        if index < len(sys.argv) - 1:
            return sys.argv[index + 1]


if __name__ == '__main__':
    process_cli()

    cherrypy.engine.unsubscribe('graceful', cherrypy.log.reopen_files)
    logging.config.dictConfig(LOG_CONF)

    options = {
        'host': '0.0.0.0',
        'port': server_port,
        'minthreads': 10,
        'maxthreads': 30,
        'server_name': 'localhost',
        'shutdown_timeout': 60,
        'request_queue_size': request_queue_size,
    }

    start_server(options)
