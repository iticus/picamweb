# PiCamWeb

## About
PiCamWeb is a Python based web interface for [Raspberry Pi Camera](https://www.raspberrypi.org/products/camera-module-v2/) (both *v1* and *v2* can be used). It uses websockets for data transport and [jsmpg](https://github.com/phoboslab/jsmpeg) to render the video feed in the browser.  
[Tornado](http://www.tornadoweb.org/en/stable/) is used for the webserver and websockets, [picamera](https://github.com/waveform80/picamera) for camera recording and [ffmpeg](http://ffmpeg.org/) to encode the raw video data to MPEG1.  
The project is inspired by the [pistreaming](https://github.com/waveform80/pistreaming) project.  
If you need authentication for the video stream you can check my [alfred](https://github.com/iticus/alfred) project.

## Installation
After making sure your camera module works (you can test it using `raspistill`) install dependencies:  
`sudo apt-get install libav-tools git python3-pip nginx`  
`sudo pip3 install tornado picamera`  
Copy source files, edit relevant settings in the `settings.py` module if needed and configure services:  
```
cd /var/www
sudo git clone https://github.com/iticus/picamweb
sudo chown -R pi:pi picamweb
cd picamweb
nano settings.py
sudo cp scripts/picamweb.service /etc/systemd/system/picamweb.service
sudo systemctl daemon-reload
sudo systemctl enable picamweb && sudo systemctl start picamweb
sudo cp scripts/nginx.default /etc/nginx/sites-available/default
sudo systemctl restart nginx
```  
Your camera feed should now be available under:  
`http://RPI_ADDRESS/`  
Useful debug command (to view application log):  
`sudo journalctl -u picamweb.service`  
## Notes
 - *jsmpg* and *ffmpeg* were chosen in order to minimize network traffic when viewing the camera feed  
 - *ffmpeg* is running in the background all the time (even when the web interface is not being accessed) which can be quite CPU intensive especially on older single-core Raspberry Pi models; that being said, it works on a *Raspberry Pi 1 Model B+* with a system load of ~ **1.2** - **1.3**  
 - an option to load ffpmeg *on demand* might be introduced in the future  
