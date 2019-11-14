"""
Created on Aug 28, 2018

@author: ionut
"""

import datetime
import logging
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler

import camera


class HomeHandler(RequestHandler):
    """
    Handler for / - render index.html
    """

    def get(self):
        camset = self.application.config.CAMERA
        self.render("index.html", width=camset["width"], height=camset["height"])


class VideoHandler(WebSocketHandler):
    """
    WebSocket Handler for /video - send video frames to connected clients
    """

    clients = set()
    last_packet = datetime.datetime.now()

    def select_subprotocol(self, subprotocols):
        logging.info("got subprotocols %s", subprotocols)
        subprotocol = subprotocols[0] if subprotocols else None
        return subprotocol

    def open(self):
        if not self.application.camera:
            self.application.camera = camera.Camera(self.application.config.CAMERA, self, self.application.io_loop)
            self.application.camera.start()
        logging.info("new ws client %s", self)
        VideoHandler.clients.add(self)

    def on_close(self):
        logging.info("removing ws client %s", self)
        VideoHandler.clients.remove(self)

    def on_message(self, message):
        logging.info("got ws message %s from %s", message, self)

    @classmethod
    def broadcast(cls, data):
        """
        Send video data to all connected web sockets and remove closed sockets
        :param cls: class method
        :param data: video data from camera brodcast thread
        """
        removable = set()
        for client in VideoHandler.clients:
            try:
                client.write_message(data, binary=True)
                VideoHandler.last_packet = datetime.datetime.now()
            except Exception as exc:
                logging.warning("loop closed for %s: %s", client, exc)
                removable.add(client)

        for client in removable:
            VideoHandler.clients.remove(client)
