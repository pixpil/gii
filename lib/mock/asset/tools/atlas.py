#!/usr/bin/env python

import os
import time
import pickle
import hashlib
import subprocess

from PIL import Image

CACHE_DIR = '~/.cache/AtlasGenerator'

def D(fmt, *args, **kwargs):
	print((str(fmt).format(*args, **kwargs)))

class Stopwatch:
	def __init__(self):
		pass

	def __str__(self):
		return "{0:.3f}".format(self.t())

	def __enter__(self):
		self.start_time = time.time()
		return self

	def __exit__(self, type, value, traceback):
		pass

	def t(self):
		return time.time() - self.start_time

class MultitaskWorker:
	def __init__(self, max_workers=None):
		import threading
		max_workers = self.get_max_workers_number() if max_workers is None else max_workers
		self.workers_semaphore = threading.BoundedSemaphore(max_workers)

	def get_max_workers_number(self):
		import multiprocessing
		return multiprocessing.cpu_count() * 2

	def _worker_body(self, function, args, kwargs):
		function(*args, **kwargs)
		self.workers_semaphore.release()

	def run_functions(self, params):
		import threading

		with Stopwatch() as s:
			self.threads = []
			for (function, args, kwargs) in params:
				self.workers_semaphore.acquire()
				t = threading.Thread(target=self._worker_body, args=(function, args, kwargs))
				t.start()
				self.threads.append(t)

			for t in self.threads:
				t.join()

			D("Finished {0} tasks in {1} seconds, {2} sec per task avg", len(params), s, s.t()/len(params))

	def _shell_worker_body(self, args):
		with Stopwatch() as s:
			subprocess.check_call(args)
			args = [a.split('/')[-1] for a in args]
			D("SHELL: '{0}' in {1} seconds", " ".join(args), s)

	def run_shell_commands(self, args_list):
		params = []
		for args in args_list:
			params.append((self._shell_worker_body, (args,), {}))

		self.run_functions(params)

def generate_files_list(paths):
	flist = []
	for path in paths:
		if os.path.isdir(path):
			for (root, dirs, files) in os.walk(path):
				for fname in files:
					fpath = os.path.join(root, fname)
					flist.append(fpath)

		elif os.path.isfile(path):
			flist.append(path)

		else:
			raise Exception("Unknown path: {0}".format(path))

	return flist

class Img:
	def __init__(self, path, fw, fh, bbox):
		self.path = path                     # path to the image file
		self.bbox = bbox                     # bbox info in format (left, top, right, bottom)
		self.x = None                        # x offset of image in the atlas
		self.y = None                        # y offset of image in the atlas
		self.fw = fw                         # full width
		self.fh = fh                         # full height
		self.w = self.bbox[2] - self.bbox[0] # bbox (cropped) width
		self.h = self.bbox[3] - self.bbox[1] # bbox (cropped) height

	def getSpriteInfo(self):
		return (self.x, self.y, self.w, self.h, self.fw, self.fh)

	def getBBoxInfo(self):
		return self.bbox

	def getImage(self):
		im = Image.open(self.path)
		im = im.crop(self.bbox)
		return im

class Node:
	def __init__(self, root, x, y, w, h):
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.img = None
		self.child1 = None
		self.child2 = None
		self.root = root or self

	def isParent(self):
		return self.child1 is not None or self.child2 is not None

	def isLeaf(self):
		return not self.isParent()

	def insert(self, img, spacing):
		if self.isParent():
			# try insert into one of the children
			return self.child1.insert(img, spacing) or self.child2.insert(img, spacing)

		else:
			if self.img is not None:
				return # node is occupied

			if self.w == img.w and self.h == img.h:
				self.img = img
				self.img.x = self.x
				self.img.y = self.y
				img.node = self
				return self # perfect fit

			if self.w < img.w or self.h < img.h:
				return # does not fit

			dw = self.w - img.w
			dh = self.h - img.h

			if dw > dh:
				# split horizontally
				self.child1 = Node( self.root, self.x, self.y, img.w, self.h)
				self.child2 = Node( self.root, self.x+img.w+spacing, self.y, self.w-img.w-spacing, self.h)
			else:
				# split vertically
				self.child1 = Node( self.root, self.x, self.y, self.w, img.h)
				self.child2 = Node( self.root, self.x, self.y+img.h+spacing, self.w, self.h-img.h-spacing)

			return self.child1.insert(img, spacing)

	def paintOn(self, canvas):
		if self.img is not None:			
			im = self.img.getImage()
			if im.mode != canvas.mode:
				im = im.convert(canvas.mode)
			canvas.paste(im, (self.x, self.y, self.x+self.w, self.y+self.h))

		if self.child1 is not None:
			self.child1.paintOn(canvas)
		if self.child2 is not None:
			self.child2.paintOn(canvas)

	def dumpImages(self):
		if self.img is not None:
			return [self.img]

		images = []

		if self.child1 is not None:
			images += self.child1.dumpImages()
		if self.child2 is not None:
			images += self.child2.dumpImages()

		return images

class AtlasGenerator:
	def __init__(self, prefix, size, **kwargs):
		self.prefix = prefix # prefix path of output atlases
		self.size = size # size of the resulting atlases
		self.crop_bbox = kwargs.get('crop_bbox', False) # crop transparent outside regions
		self.alpha_cropper = kwargs.get('alpha_cropper', True) # crop pixels with alpha = 0, not just with RGBA = 0
		self.premultiplied_alpha = kwargs.get('premultiplied_alpha', False)
		self.spacing = kwargs.get('spacing', 0) # minimal space between images in atlas, in pixels
		self.dry_run = kwargs.get('dry_run', False)
		self.quiet = kwargs.get('quiet', False)
		self.pixel_type = 'RGBA'

		self.cache_hits = 0
		self.cache_misses = 0
		self.bbox_cache_dir = os.path.expanduser(CACHE_DIR)
		try:
			os.makedirs(self.bbox_cache_dir)
		except:
			pass

	def getFileID(self, path):
		abspath = os.path.abspath(path)
		st = os.stat(path)
		s = "{p} {i} {s} {c} {m}".format(p=path, i=st.st_ino, s=st.st_size, c=st.st_ctime, m=st.st_mtime)
		m = hashlib.md5()
		m.update(s)
		h = m.hexdigest()
		#print(st, s, h)
		return h

	def getBBoxFromCache(self, path, im):
		cache_path = os.path.join(self.bbox_cache_dir, self.getFileID(path))
		if os.path.exists(cache_path):
			self.cache_hits += 1
			try:
				with open(cache_path, 'r') as f:
					return pickle.load(f)
			except:
				os.remove(cache_path)

		self.cache_misses += 1


		bbox = self.getImageBBox(im)


		with open(cache_path, 'w') as f:
			pickle.dump(bbox, f)

		return bbox

	def generateImagesInfo(self, files):
		infos = []
		for f in files:
			try:
				im = Image.open(f)
			except:
				continue

			if im.mode != self.pixel_type:
				im = im.convert(self.pixel_type)
			#print(f, im.format, im.mode)
			(w, h) = im.size
			#bbox = self.getImageBBox(im) if self.crop_bbox else (0, 0, w, h)
			bbox = self.getBBoxFromCache(f, im) if self.crop_bbox else (0, 0, w, h)
			img = Img(f, w, h, bbox)
			#img.bbox = bbox
			#img.path = f
			infos.append(img)

		return infos

	def getImageBBox(self, img):
		if not self.alpha_cropper:
			return img.getbbox()

		(w, h) = img.size
		pixels = img.load()
		for x in range(w):
			for y in range(h):
				(r, g, b, a) = pixels[x, y]
				if a == 0:
					pixels[x, y] = (0, 0, 0, 0)

		bb = img.getbbox()
		if bb is None:
			return (0, 0, 1, 1)

		return bb

	def generateAtlases(self, images):
		atlases = []
		for img in images:
			node = None
			for atlas in atlases:
				node = atlas.insert(img, self.spacing)
				if node is not None:
					break

			if node is None:
				new_atlas = Node(None, 0, 0, self.size[0], self.size[1])
				node = new_atlas.insert(img, self.spacing)
				if node is None:
					print(("ERROR: failed to insert image {0}".format(img.path)))
				else:
					atlases.append(new_atlas)

		return atlases

	def paintAtlas(self, atlas, atlas_fname):
		with Stopwatch() as s:
			canvas = Image.new(self.pixel_type, self.size, (0, 0, 0, 0))
			atlas.paintOn(canvas)
			canvas.save(atlas_fname, 'PNG')
			D("        saved atlas image file '{0}' in {1} seconds", atlas_fname, s)

	def generate(self, paths):
		D("Generating atlases with prefix '{0}'", self.prefix)

		with Stopwatch() as s:
			image_files = generate_files_list(paths)
			if len(image_files) == 0:
				D("No files found")
				return

			D("    found {0} files in {1} seconds", len(image_files), s)

		with Stopwatch() as s:
			image_infos = self.generateImagesInfo(image_files)
			image_infos = sorted(image_infos, key=lambda ii: (ii.w * ii.h), reverse=True)
			D("    done reading images metadata in {0} seconds", s)

		with Stopwatch() as s:
			atlases = self.generateAtlases(image_infos)
			D("    generated {0} atlas maps in {1} seconds", len(atlases), s)

		tilesets_info = []
		sprites_info = []
		params = []
		for (i, atlas) in enumerate(atlases):
			atlas_fname = self.prefix+"{0}.png".format(i)

			params.append((self.paintAtlas, (atlas, atlas_fname), {}))

			images = atlas.dumpImages()

			tilesets_info += [(atlas_fname, atlas.w, atlas.h, 0)]
			sprites_info += [(atlas_fname, ii.path, ii.getSpriteInfo(), ii.bbox) for ii in images]

		if not self.dry_run:
			MultitaskWorker().run_functions(params)

		return (tilesets_info, sprites_info)

def main():
	import sys
	import csv
	from optparse import OptionParser
	from pprint import pprint as pp

	parser = OptionParser(
		usage = "%prog [options] <width> <height> <paths...>",
		description = "A texture atlas generator. Specify desired width and height of the output images and paths of directories and files to look for images. Generator will produce atlas images and text file with pixel coordinates."
	)
	parser.add_option("-n", "--dry-run", action="store_true", default=False, help="Do not write files.")
	parser.add_option("-s", "--spacing", default='0', help="Spacing between textures in atlas, in pixels. Default is 0.")
	parser.add_option("-p", "--prefix", default='atlas', help="Prefix output files with this path prefix. Examples: '/tmp/tex', 'atl'. Default is 'atlas'.")
	#parser.add_option("-c", "--crop", action="store_true", default=False, help="Crop transparent borders of images to increase packing density. Default is not to crop.")
	#parser.add_option("-q", "--quiet", action="store_true", default=False, help="Do not print anything to the stdout.")

	(options, args) = parser.parse_args()
	#print(options, args)

	try:
		options.spacing = int(options.spacing)
		w = int(args[0])
		h = int(args[1])
		paths = args[2:]
		if len(paths) < 1:
			raise Exception

	except:
		parser.print_help()
		return

	agen = AtlasGenerator(
		options.prefix,
		(w, h),
		dry_run=options.dry_run,
		spacing=options.spacing,
#        quiet=options.quiet
	)
	metainfo = agen.generate(paths)

	if not options.dry_run and metainfo is not None:
		(atlases_info, images_info) = metainfo
		meta_fname = options.prefix+'.txt'
		with open(meta_fname, 'wb') as f:
			metawriter = csv.writer(f, delimiter='\t')#, quotechar='|', quoting=csv.QUOTE_MINIMAL)
			for (atl, img, (x, y, w, h, fw, fh), bbox) in images_info:
				r = [atl, img, x, y, w, h]
				metawriter.writerow(r)

			D("Metadata saved to file '{0}'", meta_fname)

if __name__ == "__main__":
	main()