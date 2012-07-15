#!/usr/bin/env python
# PyWebShot - create webpage thumbnails. Originally based on 
# http://burtonini.com/computing/screenshot-tng.py
# Ben Dowling - http://www.coderholic.com
# Further customized:
# Meatballs - http://rewtdance.blogspot.com

import os
import sys
import socket
try:
	import gtk
	import gtk.gdk as gdk
except:
	print "No GTK installed"
try:
	import gtkmozembed
except: 
	print "No gtkmozembed try: apt-get install python-gtkmozembed"
import gobject
import urlparse
import urllib2
from optparse import OptionParser

class PyWebShot:
	def __init__(self, urls, screen, thumbnail, delay, outfile, path, allow_javascript):
		self.parent = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.parent.set_border_width(0)
		self.urls = urls
		self.delay = delay
		self.path = path
		self.thumbnail_resolution = thumbnail
		self.allow_javascript = allow_javascript

		# Get resoltion information
		(x,y) = screen.split('x')
		x = int(x)
		y = int(y)
		
		self.widget = gtkmozembed.MozEmbed()
		self.widget.set_size_request(x-20, y-20)
		self.widget.set_chrome_mask(gtkmozembed.FLAG_ALLCHROME-gtkmozembed.FLAG_SCROLLBARSON)
		
		# Connect signal
		self.widget.connect("net_stop", self.on_net_stop)
		if outfile:
			(self.outfile_base, ignore) = outfile.split('.png')
		else:
			self.outfile_base = None
		self.parent.add(self.widget)
		if screen == get_screen_resolution():
			self.parent.fullscreen()
		self.parent.show_all()
		self.url_num = 0
		self.load_next_url()

	def load_next_url(self):
		if self.url_num > len(self.urls) - 1:
			gtk.main_quit()
			return
		self.current_url = self.urls[self.url_num]
		self.parent.set_title(self.current_url)
		self.countdown = self.delay
		print "Loading " + self.current_url + "...", 
		self.url_num += 1
		request = urllib2.Request(self.current_url)
		html = ""
		try:
			fd = urllib2.urlopen(request)
			if not fd.geturl() in self.current_url:
				print "Redirected to {0} ...".format(fd.geturl())
				self.current_url = fd.geturl()
			try:
				html = fd.read()
			except socket.error as e:
				print e	
			finally:
				fd.close()
		except urllib2.HTTPError as e:
			html = e.read()
			e.close()
		except urllib2.URLError as e:
			print e
		# Some Javascript causes Seg Fault
		if not self.allow_javascript:
			html = strip_javascript(html)
		self.widget.render_data(html, len(html), self.current_url, "text/html")
		
	def on_net_stop(self, data = None):
		if self.delay > 0: gobject.timeout_add(100,self.do_countdown,self)
		else: self.do_countdown()

	def do_countdown(self, data = None):
		self.countdown -= 0.1
		if(self.countdown > 0):
			return True
		else:
			self.screenshot()
			self.load_next_url()
			return False

	def screenshot(self, data = None):
		window = self.widget.window
		(x,y,width,height,depth) = window.get_geometry()
		pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,width,height)
		pixbuf.get_from_drawable(window,self.widget.get_colormap(),0,0,0,0,width,height)
		
		if self.outfile_base:
			if len(self.urls) == 1:
				filename = "%s.png" % (self.outfile_base)
			else:
				filename = "%s-%d.png" % (self.outfile_base, self.url_num)
		else:
			parts = urlparse.urlsplit(self.current_url)
			filename = parts.netloc + parts.path.replace('/', '_') + ".png"

		file_path = "{0}/{1}".format(self.path, filename)
		try:
			pixbuf.save(file_path,"png")
			print "Saved as " + filename + " to " + self.path
		except Exception as e:
			print e

                if self.thumbnail_resolution:
                        (t_x, t_y) = self.thumbnail_resolution.split('x')
                        t_x = int(t_x)
                        t_y = int(t_y)
                        # Calculate the x scale factor
                        scale_x = float(t_x) / width
                        scale_y = float(t_y) / height
                        scale = scale_x
		        thumbnail = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,t_x,t_y)
                	pixbuf.scale(thumbnail, 0, 0, t_x, t_y, 0, 0, scale, scale, gdk.INTERP_HYPER)
			thumb_filename = "thumb-{0}".format(filename)
	                thumb_path = "{0}/{1}".format(self.path, thumb_filename)
        	        thumbnail.save(thumb_path,"png")
			print "Saved thumbnail as " + thumb_filename


		return True

def strip_javascript(html):
	import re
	script_tag = re.compile("<script(.*?)</script>", re.IGNORECASE+re.DOTALL)
	return script_tag.sub("",html,0)
		
def __windowExit(widget, data=None):
	gtk.main_quit()

def validate_urls(urls):
	valid_urls = []
	
	for url in urls:
		if url[0:4] != "http":
			url = "http://{0}".format(url)

		o = urlparse.urlparse(url)
		if not o.scheme and not o.netloc:
			print "Invalid URL: %s will not be processed" % (url)
		else:
			valid_urls.append(url)
	return valid_urls

def get_screen_resolution():
	width = gtk.gdk.screen_width()
	height = gtk.gdk.screen_height()
	return "{0}x{1}".format(width, height)

def take_screenshots(urls, resolution=get_screen_resolution(), thumb_resolution=None, delay=0.01, filename=None, path=os.getcwd(), allow_javascript=False):
        valid_urls = validate_urls(urls)

        if len(valid_urls) > 0:
                window = PyWebShot(valid_urls, resolution, thumb_resolution, delay, filename, path, allow_javascript)
                window.parent.connect("destroy", __windowExit)
                gtk.main()
        else:
                print "No Valid URLs specified"

def main():
        usage = "usage: %prog [options] url1 [url2 ... urlN]"
        parser = OptionParser(usage=usage)
        parser.add_option('-r', '--resolution', action='store', type='string', help='Screen resolution at which to capture the webpage (default full screen resolution - %default)', default=get_screen_resolution())
        parser.add_option('-t', '--thumb-res', dest="thumbnail_resolution", action='store', type='string', help='Thumbnail resolution (default %default)', default=None)
        parser.add_option('-d', '--delay', action='store', type='int', help='Delay in seconds to wait after page load before taking the screenshot (default %default)', default=0.01)
        parser.add_option('-f', '--filename', action='store', type='string', help='PNG output filename with .png extension, otherwise default is based on url name and given a .png extension')
        parser.add_option('-p', '--path', action='store', type='string', help='Output path (default pwd)', default=os.getcwd())
        parser.add_option('-j', '--allow-jscript', action='store_true', dest='jscript', default=False, help='Allow Javascript (default %default)')
        (options,args) = parser.parse_args()

        if len(args) == 0:
                print "No URL specified"
                parser.print_help()
                return None

        take_screenshots(args, options.resolution, options.thumbnail_resolution, options.delay, options.filename, options.path, options.jscript)

if __name__ == "__main__":
	main()
