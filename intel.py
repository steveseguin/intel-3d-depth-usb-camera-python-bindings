import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import numpy as np
import cv2
import datetime
import sys
import urllib2
from socket import socket, AF_INET, SOCK_DGRAM

GObject.threads_init()
Gst.init(None)
global im_gray
im_gray = None

def on_new_buffer1(appsink):
	global im_gray
	w=628
	h=429
	size=w*h
	sample = appsink.emit('pull-sample')
	#get the buffer
	buf=sample.get_buffer()
	print buf.get_size(),size
	#extract data stream as string
	data=buf.extract_dup(0,buf.get_size())
	stream=np.fromstring(data,np.uint16) #convert data form string to numpy array // THIS IS YUV , not BGR.  improvement here if changed on gstreamer side
	im_gray=stream[0:size].reshape(h,w) # create the y channel same size as the image
	np.save("depth_c.i3d",im_gray)
	cv2.imshow("show",im_gray[:,:]*12)
	cv2.waitKey(1)
	return False

	
def on_new_buffer2(appsink2):
	global image
	w=640*2
	h=480
	size=w*h
	sample = appsink2.emit('pull-sample')
	#get the buffer
	buf=sample.get_buffer()
	print buf.get_size(),size
	#extract data stream as string
	data=buf.extract_dup(0,buf.get_size())
	stream=np.fromstring(data,np.uint8) #convert data form string to numpy array // THIS IS YUV , not BGR.  improvement here if changed on gstreamer side
	image=stream[0:size*2:2].reshape(h,w/2) # create the y channel same size as the image
	#np.save("yuv_c.i3d",stream.reshape(h,w))
	cv2.imshow("show2",image)
	cv2.waitKey(1)
	return False


def on_new_buffer0(appsink):
	global im_gray
	x=3
	w=640
	h=481
	size=w*h
	sample = appsink.emit('pull-sample')
	#get the buffer
	buf=sample.get_buffer()
	print buf.get_size(),size
	#extract data stream as string
	data=buf.extract_dup(0,buf.get_size())
	#data = np.array(data, dtype=np.uint16)
	#data1 = data[0::3] + data[1::3])
	
	#bin_chunks = [data[12*i:12*(i+1)] for i in xrange(len(data)//12)]
	#ints = [int(x, 2) for x in bin_chunks]
	#stream = np.array(ints, dtype=np.uint16)
	stream = np.fromstring(data, dtype=np.uint8)
	#stream = stream.astype(np.uint16)
	#stream1 = stream[2::3]*256
	#stream1 = stream[2::x]*4 # + stream[0::3]*64
	stream1 = (stream[1::x]<<4).astype(np.uint16)*16 + stream[0::x].astype(np.uint16) #+ stream[2::x]*4 
	stream1*=64
	stream2 = (stream[1::x]>>4).astype(np.uint16) + stream[2::x].astype(np.uint16)*16 #+ stream[2::x]*4 
	stream2*=64
	#stream[1::3] = (stream1[1::3] & 0x0f)*16 + stream1[2::3]
	
	#stream= [data[i:i+n] for i in range(0, len(data), n)]
	#np.left_shift(np.fromstring(data[0::3],np.uint8).astype(np.uint16),4) + np.right_shift(np.fromstring(data[1::3],np.uint8),4).astype(np.uint16)#convert data form string to numpy array // THIS IS YUV , not BGR.  improvement here if changed on gstreamer side
	im_gray1=stream1[0:size].reshape(h,w) # create the y channel same size as the image
	im_gray2=stream2[0:size].reshape(h,w) # create the y channel same size as the image
	im_gray3=np.vstack((im_gray1,im_gray2)).reshape(h*2,w)
	np.save("stereo_full_c.i3d",im_gray3)
	#print np.max(im_gray1)
	#im_gray1[np.where(im_gray1<65472)]=0
	#cv2.imshow("show1",im_gray1[:,:])
	#cv2.imshow("show2",im_gray2[:,:])
	cv2.imshow("show3",im_gray3[:,:])
	cv2.waitKey(1)
	return False

CLI2="ksvideosrc device-index=2 ! video/x-raw,format=YUY2,width=640,height=480,framerate=60/1 ! appsink name=sink2" ## 60 FPS
#CLI2="ksvideosrc device-index=1 ! video/x-raw,width=628,height=469,framerate=30/1 ! appsink name=sink2"
pipline2=Gst.parse_launch(CLI2)
appsink2=pipline2.get_by_name("sink2")
appsink2.set_property("max-buffers",20) # prevent the app to consume huge part of memory
appsink2.set_property('emit-signals',True) #tell sink2 to emit signals
appsink2.set_property('sync',False) #no sync to make decoding as fast as possible
appsink2.set_property('drop', True) ##  qos also
appsink2.set_property('async', True)
appsink2.connect('new-sample', on_new_buffer2) #connect signal to callable func
pipline2.set_state(Gst.State.PLAYING)
bus2 = pipline2.get_bus();
msg2 = bus2.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)


#CLI="ksvideosrc device-index=0 ! video/x-raw,format=RW10,width=2400,height=1081 ! appsink name=sink"

#####
#CLI="ksvideosrc device-index=0 ! video/x-raw,format=Y12I,width=640,height=481,framerate=60/1 ! videoparse format=GST_VIDEO_FORMAT_GRAY16_LE width=640 height=480 ! autovideoconvert ! videomixer name=mixme ! appsink name=sink ksvideosrc device-index=2 ! video/x-raw,format=YUY2,width=640,height=480,framerate=60/1 ! videoparse format=GST_VIDEO_FORMAT_GRAY16_LE width=640 height=480 ! autovideoconvert ! mixme."
#CLI="gst-launch -e videomixer name=mix sink_0::xpos=0 sink_0::ypos=0 sink_0::alpha=0 sink_1::xpos=640 sink_1::ypos=0 ! appsink name=sink videotestsrc ! video/x-raw-yuv,width=640,height=480 ! mix.sink_0 videotestsrc pattern=0 ! video/x-raw-yuv,width=640,height=480 ! mix.sink_1 "
#CLI="videomixer name=mix sink_0::xpos=0 sink_0::ypos=0 sink_1::xpos=640 sink_1::ypos=0 ! appsink name=sink ksvideosrc device-index=2 ! video/x-raw,format=YUY2,width=640,height=480,framerate=60/1 ! mix.sink_0  ksvideosrc device-index=0 ! video/x-raw,format=YUY2,width=320,height=962,framerate=60/1 ! mix.sink_1"

CLI="ksvideosrc device-index=0 ! video/x-raw,format=Y12I,width=640,height=481,framerate=90/1 ! appsink name=sink" ## 60 FPS // STEREO
pipline=Gst.parse_launch(CLI)
appsink=pipline.get_by_name("sink")
appsink.set_property("max-buffers",20) # prevent the app to consume huge part of memory
appsink.set_property('emit-signals',True) #tell sink to emit signals
appsink.set_property('sync',False) #no sync to make decoding as fast as possible
appsink.set_property('drop', True) ##  qos also
appsink.set_property('async', True)
appsink.connect('new-sample', on_new_buffer0) #connect signal to callable func
pipline.set_state(Gst.State.PLAYING)
bus = pipline.get_bus();
msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)