import os, sys, random, re, subprocess, shlex, atexit, threading
TMP_DIR = "./"#os.popen('mktemp -d').read().replace('\n', '')

from youtube_dl import _real_main as yt_dl_main

atexit.register(lambda: os.system('rm -r "%s"' % TMP_DIR))

def tmpfile_path():
	return TMP_DIR + '/' + ''.join([random.choice(list('0123456789abcdef')) for i in range(16)])

def system_(cmd):
	print(cmd)
	p = subprocess.Popen(shlex.split(cmd), stderr=subprocess.PIPE, shell=False, bufsize=-1)
	p.wait()
	if p.returncode != 0:
		raise OSError('Command returned {}: `{}`\n\n{}'.format(p.returncode, cmd, p.stderr.read().decode('utf-8')))

class Downloader (threading.Thread):
	def __init__(self, video_url: str, quality: str = '7', search = False):
		threading.Thread.__init__(self, target=self.get_yt_url)
		self.error = None
		self.data  = None

		self.video_url = video_url
		self.quality = quality
		self.search = search
	def get_yt_url(self):
		try:
			filename = tmpfile_path()

			quality: int = int(self.quality)
			wide: bool = quality > 7
			quality = quality if not wide else quality - 8

			amr_ext = 'amr-nb' if not wide else 'amr-wb'

			# Download
			if self.search or self.video_url.startswith('http'):#re.match('^http(s?):\/\/(www.)?(youtube|youtu.be).[a-z.]{2,}\/', self.video_url):
				legit_exit = sys.exit
				sys.exit = lambda *args: None
				yt_dl_main(argv=['--extract-audio', '-o', filename + '.%(ext)s', '{}{}'.format('ytsearch1:' if self.search else '', self.video_url)])
				sys.exit = legit_exit
				system_('mv {} {}'.format(TMP_DIR + '/' + next(f for f in os.listdir(TMP_DIR) if f.startswith(filename.split('/')[-1])), filename))       # Gets rid of extension. We can't use wildcards so we have to use this garbage.
			else:
				system_('wget "{}" -O {}'.format(self.video_url, filename))

			# Convert
			system_('ffmpeg -i {0} -filter:a "volume=0.9" {0}.wav'.format(filename))
			system_('sox {0}.wav -C {qual} {0}.{amr_ext}'.format(filename, qual=quality, amr_ext=amr_ext))

			# Read AMR into memory
			self.data = open('{}.{}'.format(filename, amr_ext), 'rb').read()

			# Clean up
			system_('rm {}'.format(' '.join([TMP_DIR + '/' + f for f in os.listdir(TMP_DIR) if f.startswith(filename.split('/')[-1])])))	# AMR won't be deleted as it's in amr/ directory
		except OSError as err:
			self.error = err
