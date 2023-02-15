sudo apt-get -y install python3-psutil
sudo apt-get -y install python3-pyqtgraph

option
sudo apt-get -y install python3-docker


sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly

gst-launch-1.0 -v udpsrc port=11111 caps="video/x-h264, stream-format=(string)byte-stream" ! decodebin ! videoconvert ! autovideosink sync=false


option
gst-launch-1.0 -v udpsrc port=11118 caps="video/x-h264, stream-format=(string)byte-stream" ! decodebin ! videoconvert ! autovideosink sync=false
