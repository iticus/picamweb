"""
Created on Aug 28, 2018

@author: ionut
"""

import logging
import threading
import time
from subprocess import Popen, PIPE, DEVNULL
import picamera


class BroadcastOutput:
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
                "-f", "mpegts",
                "-codec:v", "mpeg1video",
                "-an",
                "-b", "800k",
                "-r", str(float(camera.framerate)),
                "-"
            ],
            stdin=PIPE, stdout=PIPE, stderr=DEVNULL, shell=False, close_fds=True
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


class Camera:

    def __init__(self, camset, wso, io_loop):
        self.camset = camset
        self.wso = wso
        self.io_loop = io_loop
        self.camera = None
        self.output = None
        self.broadcast_thread = None

    def start(self):
        logging.info("initializing camera")
        self.camera = picamera.PiCamera()
        self.camera.resolution = (self.camset["width"], self.camset["height"])
        self.camera.framerate = self. camset["framerate"]
        self.camera.vflip = self.camset["vflip"]
        self.camera.hflip = self.camset["hflip"]
        time.sleep(1)  # camera warm-up time
        self.output = BroadcastOutput(self.camera)
        logging.info("starting broadcast thread")
        self.broadcast_thread = BroadcastThread(self.output.converter, self.wso, self.io_loop)
        self.camera.start_recording(self.output, "yuv")
        self.broadcast_thread.start()
        return self

    def stop(self):
        logging.info("stopping broadcast thread")
        self.broadcast_thread.stop()
        logging.info("stopping output process")
        self.output.flush()
        logging.info("closing camera object")
        self.camera.close()
