"""
Created on Aug 28, 2018

@author: ionut
"""

import logging
import signal
import sys
import tornado

import camera
import handlers
import settings
import utils


def app_exit():
    """Stop IOLoop and exit"""
    tornado.ioloop.IOLoop.instance().stop()
    logging.info("finished")
    sys.exit()


def cleanup_hook(exc_type, exc_value, exc_traceback):
    """Log exception details and call app_exit"""
    logging.error("Uncaught exception, stopping", exc_info=(exc_type, exc_value, exc_traceback))
    app_exit()


def configure_signals():
    """Configure signal handling to cleanly exit the application"""

    def stopping_handler(signum, frame):
        """Log frame details and call app_exit"""
        frame_data = utils.format_frame(frame)
        logging.info("interrupt signal %s, frame %s received, stopping", signum, frame_data)
        app_exit()

    signal.signal(signal.SIGINT, stopping_handler)
    signal.signal(signal.SIGTERM, stopping_handler)


def make_app(io_loop=None):
    """
    Create and return tornado.web.Application object so it can be used in tests too
    :param io_loop: already existing ioloop (used for testing)
    :returns: application instance
    """
    app = tornado.web.Application(
        [
            (r"/", handlers.HomeHandler),
            (r"/video/?", handlers.VideoHandler)
        ],
        template_path=settings.TEMPLATE_PATH,
        static_path=settings.STATIC_PATH,
    )
    if not io_loop:
        io_loop = tornado.ioloop.IOLoop.current()
    cam = camera.Camera(settings.CAMERA, handlers.VideoHandler, io_loop)
    cam.start()
    app.camera = cam
    app.config = settings
    app.cache = {}
    app.io_loop = io_loop
    return app


def main():
    """Start camera and Tornado application instance"""
    application = make_app()
    logging.info("starting picamweb on %s:%s", application.config.ADDRESS, application.config.PORT)
    application.listen(application.config.PORT, address=application.config.ADDRESS)
    if application.io_loop:
        application.io_loop.start()
    else:
        tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    sys.excepthook = cleanup_hook
    configure_signals()
    main()
