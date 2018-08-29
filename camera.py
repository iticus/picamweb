"""
Created on Aug 28, 2018

@author: ionut
"""

import io
import logging
import os
import threading
import time
from subprocess import Popen, PIPE
import picamera


class BroadcastOutput():
    """
    Run background ffmpeg process to generate MPEG1 data from picamera
    """


    def __init__(self, camera):
        logging.info("spawning background conversion process")
        self.converter = Popen(
            [
                "ffmpeg",
                "-f", "rawvideo",
                "-pix_fmt", "yuv420p",
                "-s", "%dx%d" % camera.resolution,
                "-r", str(float(camera.framerate)),
                "-i", "-",
                "-f", "mpeg1video",
                "-b", "800k",
                "-r", str(float(camera.framerate)),
                "-"
            ],
            stdin=PIPE, stdout=PIPE, stderr=io.open(os.devnull, "wb"),
            shell=False, close_fds=True
        )


    def write(self, data):
        """
        Write data output
        :param data: video data to write
        """
        self.converter.stdin.write(data)


    def flush(self):
        """
        Close ffmpeg process
        """
        logging.info("waiting for background conversion process to exit")
        self.converter.stdin.close()
        self.converter.wait()


class BroadcastThread(threading.Thread):
    """
    Broadcast thread to read from ffmpeg output and send to connected websockets (wso)
    """


    def __init__(self, converter, wso, ioloop):
        super(BroadcastThread, self).__init__()
        self.converter = converter
        self.wso = wso
        self.ioloop = ioloop


    def run(self):
        try:
            while True:
                data = self.converter.stdout.read1(32768)
                if data:
                    def callback():
                        self.wso.broadcast(data)
                    self.ioloop.add_callback(callback=callback)
                elif self.converter.poll() is not None:
                    break
        finally:
            self.converter.stdout.close()


def init(camset, wso, ioloop):
    """
    Initialize camera and broadcast thread
    :param camset: camera settings object (from settings module)
    :param wso: WebSocket handler to use for broadcasting data
    :param ioloop: tornado IOLoop instance
    """
    logging.info("initializing camera")
    camera = picamera.PiCamera()
    camera.resolution = (camset["width"], camset["height"])
    camera.framerate = camset["framerate"]
    camera.vflip = camset["vflip"]
    camera.hflip = camset["hflip"]
    time.sleep(1) # camera warm-up time
    output = BroadcastOutput(camera)
    logging.info("starting broadcast thread")
    broadcast_thread = BroadcastThread(output.converter, wso, ioloop)
    camera.start_recording(output, "yuv")
    broadcast_thread.start()
    return camera, broadcast_thread
