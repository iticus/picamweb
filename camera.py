"""
Created on Aug 28, 2018

@author: ionut
"""

# import datetime
import logging
import threading
import time
from io import BytesIO
from subprocess import Popen, PIPE, DEVNULL
import picamera


class ImageBroadcastThread(threading.Thread):
    """
    Broadcast thread to read from image data and send to connected websockets (wso)
    """

    def __init__(self, camera, wso, io_loop):
        super(ImageBroadcastThread, self).__init__()
        self.camera = camera
        self.output = BytesIO()
        self.wso = wso
        self.io_loop = io_loop
        self.running = True

    def run(self):
        try:
            while self.running:
                self.output.seek(0)
                self.camera.capture(self.output, "jpeg", quality=15, thumbnail=None, bayer=False)
                data = self.output.getvalue()
                self.output.truncate(0)
                logging.debug("got %d bytes of image data from camera", len(data))
                if data:
                    def callback():
                        self.wso.broadcast(data)
                    self.io_loop.add_callback(callback=callback)
                time.sleep(0.01)
        finally:
            self.output.close()

    def stop(self):
        self.running = False


class VideoBroadcastOutput:
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


class VideoBroadcastThread(threading.Thread):
    """
    Broadcast thread to read from ffmpeg output and send to connected websockets (wso)
    """

    def __init__(self, output, wso, io_loop):
        super(VideoBroadcastThread, self).__init__()
        self.output = output
        self.wso = wso
        self.io_loop = io_loop
        self.running = True

    def run(self):
        try:
            while self.running:
                data = self.converter.stdout.read1(32768)
                if data:
                    def callback():
                        self.wso.broadcast(data)
                    self.io_loop.add_callback(callback=callback)
                elif self.converter.poll() is not None:
                    break
        finally:
            self.converter.stdout.close()

    def stop(self):
        self.running = False


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
        if self.camset["ffmpeg"]:
            time.sleep(0.5)  # camera warm-up time
            self.output = VideoBroadcastOutput(self.camera)
            logging.info("starting broadcast thread")
            self.broadcast_thread = VideoBroadcastThread(self.output.converter, self.wso, self.io_loop)
            self.camera.start_recording(self.output, "yuv")
            self.broadcast_thread.start()
        else:
            self.camera.start_preview()
            time.sleep(0.1)
            # self.camera.annotate_background = picamera.Color("black")
            # self.camera.annotate_text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.broadcast_thread = ImageBroadcastThread(self.camera, self.wso, self.io_loop)
            self.broadcast_thread.start()
        return self

    def stop(self):
        logging.info("stopping broadcast thread")
        self.broadcast_thread.stop()
        logging.info("closing camera object")
        self.camera.close()
        logging.info("stopping output process")
        if self.output:
            self.output.flush()
