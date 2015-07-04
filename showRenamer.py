#!/usr/bin/env python
#!/usr/bin/python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import os
from base64 import b64decode as passwdDecoder
import subprocess
import shutil
import getopt
import sys
import re
import math
import json

# def is_number(s):
#     try:
#         float(s)
#         return True
#     except ValueError:
#         pass
 
#     try:
#         from unicodedata import numeric
#         numeric(s)
#         return True
#     except (TypeError, ValueError):
#         pass
#     return False

class ShowRenamer:
	# Filename characters to be ignored
	ignr = ['.',',','-','_','(',')',';',':','"',"'",'US','EXCELLENCE','x264','X264','HDTV','2HD','LOL','DIMENSION','[rartv]','[eztv]','[eetv]','WEB','DL','XviD','+','FUM','QCF','XVID','Xvid','PDTV','NoTV','WS','KILLERS','480p','720p','1080p','2HD','HD2','BAJSKORV','REPACK','EVOLVE','AAC','E-Subs','[GWC]','WebRip','WEBRip','SNEAkY','w4f','hdtv','[',']','{','}'];
	
	# Allowed file extensions
	extns = ['.mp4','.m4v','.avi','.mpg','.mkv','.mov','.mpeg']

	# Not capitalized
	nocaps = ['the','at','is','are','and','or','nor','either','neither','to','as','if','with']

	# Replace in filename
	specl_n = []	# Needle
	specl_r	= []	# Replace

	# Server
	s_user = 'Jan'	# Server user name
	s_passwd = ""	# Server password
	s_server = '192.168.0.105'	# Server address
	s_folder = 'TV%20Shows'		# Server path
	s_mount = './tempSrvMnt'		# Temporary mount directory

	# Status
	remote = False				# Copy to server
	clean = False				# Clean after copy

	# Directories
	cwd = ''		# Current working directory (file directory)
	ddir = ''		# File directory

	def __init__(self):
		self.cwd = os.getcwd()
		self.ddir = self.cwd

	def __del__(self):
		self.RemoteDisconnect()

	def GetPasswdFromFile(self):
		'''
		As a server password you can create a file ".pswd" in the directory with the output
		generated with "import base64; print(base64.b64encode(b"password"));"
		'''
		if not self.s_passwd:
			# base64 encoded password saved in .pswd 
			try:
				lines = [line.strip() for line in open('.pswd')]
				self.s_passwd = passwdDecoder(lines[0]).decode("utf-8")
			except OSError:
				pass

	def Cd(self, path):
		'''
		Change directory
		'''
		if not path:
			path = os.getcwd()
		self.ddir = str(path)
		os.chdir(self.ddir)

	def __BuildRemoteCmd(self):
		'''
		Combine samba remote string:
			'mount_smbff //user:1234@MACHINE/path ./localPath
		'''
		return 'mount_smbfs //' + self.s_user + ':' + self.s_passwd + '@'\
			+ self.s_server + '/' + self.s_folder + ' ' + self.s_mount

	def GetLocalFiles(self, extns=[]):
		if len(extns) <= 0:
			extns = self.extns
		files = [ f for f in os.listdir(self.ddir) if os.path.isfile(os.path.join(self.ddir,f))]
		files = [ f for f in files if f[len(f)-4:] in extns]
		return files

	def __ExtractSeasonEpisodes(self,f):
		f = str(f)
		res = {'s': None, 'e': None, 'f': None}
		try:
			uf = f.upper() 

			# Extract the classic S01E03
			m = re.search(' S[0-9]{1,3}E[0-9]{1,3}', uf)
			if m:
				s = m.group(0)
				s = s.replace(' ','')
				s = s[1:]
				s = s.split('E')
				res['s'] = int(s[0])
				res['e'] = int(s[1])
				res['f'] = f[:m.start(0)]
				return res

			# Extract the lazy mans 103 (sometimes movies fall through this!)
			m = re.search(' [0-9]{3,6}', uf)
			if m:
				s = m.group(0)
				s = s.replace(' ','')
				l = len(s)
				l = math.ceil(l/2)
				res['s'] = int(s[:l-1])
				res['e'] = int(s[l-1:])
				res['f'] = f[:m.start(0)]
				return res

		except:
			print('(!) Exception was thrown during meta extraction')
			res = None
			pass
		return res

	def __CapitalizeName(self,f):
		f = str(f).lower()
		first = True
		name = ''
		for n in f.split():
			if first:
				name = n.capitalize()
			elif n in self.nocaps:
				name += ' ' + n
			else:
				name += ' ' + n.capitalize()
			first = False
		return name

	def __AppendMetaString(self,meta,ext):
		name = self.__CapitalizeName(meta['f'])
		nf =  name + ' S{:02}E{:02}'.format(int(meta['s']),int(meta['e'])) + ext
		return (nf, name)

	def PrepareFilenames(self, files):
		lst = []
		# Loop all local file names
		for f in files:
			of = f # Filename + Extension
			ext = f[len(f)-4:]	# Extension
			f = f[:len(f)-4]	# Filename

			# Remove strings that should be ignored
			for rep in self.ignr:
				f = f.replace( str(rep),'')

			# Replace needle with new string
			for kl in range(len(self.specl_n)):
				f = f.replace(self.specl_n[kl], self.specl_r[kl])

			# Find Season and Expisode (SxxEyy)
			meta = self.__ExtractSeasonEpisodes(f)
			if not meta or not meta['s'] or not meta['e']:
				print( '(?) "' + of + '" is not a TV Show or uncommonly named ...')
				continue

			# New filename
			l = self.__AppendMetaString( meta, ext)
			lst.append( {'newf': l[0], 'oldf': of, 'name': l[1], 's': meta['s'], 'e': meta['e']} )

		return lst

	def RenameFiles(self, lst):
		for l in lst:
			print( '(-) Renaming file to "' + l['newf'] + '" ...')
			shutil.move( l['oldf'], l['newf'])

	def RemoteConnect(self):
		if not self.remote:
			return False

		print( '( ) Create mount point ...')
		try:
			os.system( 'mkdir ' + self.s_mount)
		except:
			print( '(!) Unable to create mount directory ...')
			self.remote = False
			return False

		print( '( ) Connecting to server ...')
		if os.system(self.__BuildRemoteCmd()) is not 0:
			print( '(!) Unable to mount remote server ...')
			os.system('rmdir ' + self.s_mount)
			self.remote = False
			return False

		return True

	def RemoteParseDirs(self):
		if not self.remote:
			return None

		if not os.path.isdir(self.s_mount):
			print( '(!) Server not mounted')
			return None

		print('( ) Parse server directories')
		os.chdir( self.s_mount)
		ls = subprocess.check_output(['ls']).decode("utf-8")
		os.chdir( '..')
		ls = ls.split('\n')
		ls = [ f for f in ls if f.find('.') < 0 or f.find('.') > 2 ]
		if len(ls) < 1:
			print( '(!) No shows available on server ...')
			self.RemoteDisconnect()
			self.remote = False
			return None

		lls = []
		for i in range(len(ls)):	
			lls.append(ls[i].lower())

			for rep in self.ignr:
				lls[i] = lls[i].replace( str(rep),'')
			
			for kl in range(len(self.specl_n)):
				lls[i] = lls[i].replace( self.specl_n[kl], self.specl_r[kl])
				ls[i] = ls[i].replace( self.specl_n[kl], self.specl_r[kl])

		return {'ls': ls, 'lls': lls}

	def RemoteMoveToServer(self, llist, lmeta):
		if not self.remote:
			return None

		if not os.path.isdir(self.s_mount):
			print( '(!) Server not mounted')
			return None

		ls = llist['ls']
		lls = llist['lls']

		if not ls or not lls or not len(ls) == len(lls):
			print( '(!) Invalid file lists')

		for meta in lmeta:
			showdir = ''
			for i in range(len(ls)):
				if lls[i].find(meta['name'].lower()) == 0:
					showdir = ls[i]
			showdir = str(showdir)
			if not showdir:
				showdir = meta['name']

			while showdir[-1:] == ' ':
				showdir = showdir[:-1]

			rf = self.s_mount.replace('./','') + '/' + str(showdir) + '/Season {:02}/'.format(int(meta['s']))
			if not os.path.isdir(rf):
				print( '(!) The directory "' + str(showdir) + '/Season {:02}/'.format(int(meta['s'])), '" doesn\'t exist on server ...')
				srf = self.s_mount.replace('./','') + '/' + str(showdir) + '/'
				if not os.path.isdir(srf):
					print( '(:) "' + str(showdir) + '" has been created on server ...')
					os.system('mkdir "' + srf + '"')
				if not os.path.isdir(rf):
					print( '(:) "' + 'Season {:02}'.format(int(meta['s'])) + '" has been created on server ...')
					os.system('mkdir "' + rf + '"')

			if os.path.isdir(rf):
				rf = rf + meta['newf']
				if os.path.isfile(rf):
					print( '(!) '+meta['name']+': File already exists on server ...')
				else:
					print( '(+) '+meta['name']+': Copying file to "', str(showdir), '/Season {:02}/'.format(int(meta['s'])), '" on server ...')
					shutil.copy( meta['newf'], rf)

				if self.clean and os.path.isfile(rf):
					print( '(-) '+meta['name']+': Deleting file on local machine ...')
					os.system('rm "' + meta['newf'] + '"')

	def RemoteDisconnect(self):
		if not self.remote:
			return
		os.system('umount ' + self.s_mount)
		os.system('rmdir ' + self.s_mount)
		self.remote = False

	def SaveSettings(self, json_path='showRenamerSettings.json'):
		if os.path.isfile(json_path):
			os.remove(json_path)

		contdict = { 'ignore_str': self.ignr, \
			 'valid_ext': self.extns, \
			 'nocaps': self.nocaps, \
			 'repl_needle': self.specl_n, \
			 'repl_replace': self.specl_r, \
			 'directory': self.ddir, \
			 'remote': { \
			 	'user': self.s_user, \
			 	'password': self.s_passwd, \
			 	'server_addr': self.s_server, \
			 	'directory': self.s_folder, \
			 	'mount_directory': self.s_mount, \
			 } \
			}
		dump = json.dumps( contdict, sort_keys=True, indent=4)

		jfile = open(json_path, "w")
		jfile.write(dump)
		jfile.close()

		print('(:) Settings saved to JSON file')

	def LoadSettings(self, json_path='showRenamerSettings.json'):
		if not os.path.isfile(json_path):
			json_path = os.path.dirname(os.path.realpath(__file__))+'/'+os.path.basename(json_path)
			if not os.path.isfile(json_path):
				print('(!) Settings file "'+json_path+'" is not present')
				return

		jfile = open(json_path, "r")
		dump = jfile.read()
		jfile.close()

		contdict = json.loads(dump)

		self.ignr = contdict['ignore_str']
		self.extns = contdict['valid_ext']
		self.nocaps = contdict['nocaps']
		self.specl_n = contdict['repl_needle']
		self.specl_r = contdict['repl_replace']
		if contdict['directory']:
			self.ddir = contdict['directory']
		self.s_user = contdict['remote']['user']
		self.s_passwd = contdict['remote']['password']
		self.s_server = contdict['remote']['server_addr']
		self.s_folder = contdict['remote']['directory']
		self.s_mount = contdict['remote']['mount_directory']

		print('(:) Settings loaded from JSON file')

def usage():
	print( ' ')
	print( ' ')
	print( 'showRenamer 2.0 by dev@lightgraffiti.de')
	print( '---------------------------------------')
	print( 'Rename downloaded TV shows, copy them from local directory to a samba share share,')
	print(' and cleanup.')
	print( ' ')
	print( 'Usage: ')
	print( ' ')
	print( '   showRenamer.py -h -r -c -d <directory> -s <remote server> -u <user> -p <password>')
	print( '                  -f <remote directory> -m <mount point>')
	print( ' ')
	print( '-h [--help]                         Show this help')
	print( '-r [--remote]                       Copy files to remote server')
	print( '-c [--cleanup]                      Delete files after copying to remote server')
	print( '-d [--directory] <directory>        Directory on loacal machine, other than current')
	print( '-s [--server] <remote server>       Server address')
	print( '-u [--user] <user>                  Server username')
	print( '-p [--password] <password>          Server password')
	print( '-f [--remotedir] <remote directory> Directory on server')
	print( '-m [--mount] <mount point>          Mount point (directory) on local machine')
	print( '-o [--settings] <settings path>    JSON file with settings')
	print( '-g [--settings_save]               Save settings to local file')
	print( ' ')
	print( ' ')
	print( 'As a server password you can create a file ".pswd" in the directory with the output')
	print( 'generated with "import base64; print(base64.b64encode(b"password"));"')
	print( ' ')
	print( ' ')
	print( 'Don\'t do bad stuff and buy things!')
	print( ' ')
	print( ' ')

if __name__ == "__main__":
	argv = sys.argv[1:]

	sr = ShowRenamer()

	try:
		opts, args = getopt.getopt(argv,"hd:u:p:s:f:m:rc:o:g")# ,["ifile=","ofile="])
	except getopt.GetoptError as err:
		print( '(!) ' + str(err))
		print( ' ')
		print( usage())
		sys.exit(2)

	settings_path = 'showRenamerSettings.json'
	for o, a in opts:
		if o in ('-o','--settings'):
			settings_path = str(a)
		else:
			continue

	sr.LoadSettings(settings_path)
	if not sr.s_passwd:
		sr.GetPasswdFromFile()

	for o, a in opts:
		if o in ('-h','--help'):
			usage()
			# sys.exit()
		elif o in ('-d','--directory'):
			sr.Cd(str(a))
			# print(ddir)
		elif o in ('-u','--user'):
			sr.s_user = str(a)
			sr.remote = True
		elif o in ('-p','--password'):
			sr.s_passwd = str(a)
			sr.remote = True
		elif o in ('-s','--server'):
			sr.s_server = str(a)
			sr.remote = True
		elif o in ('-f','--remotedir'):
			sr.s_folder = str(a)
			sr.remote = True
		elif o in ('-m','--mount'):
			sr.s_mount = str(a)
			sr.remote = True
		elif o in ('-r','--remote'):
			sr.remote = True
		elif o in ('-c','--cleanup'):
			sr.clean = True
		else:
			continue

	print( '( ) Local file directory: "' + sr.ddir + '"')

	localFiles = sr.GetLocalFiles()
	if len(localFiles) < 1:
		print( '(!) Directory doesn\'t contain any suiting files ...')
		sys.exit(1)

	names = sr.PrepareFilenames(localFiles)

	sr.RenameFiles(names)

	if sr.RemoteConnect():
		llist = sr.RemoteParseDirs()
		if llist:
			sr.RemoteMoveToServer(llist, names)
		
	sr.RemoteDisconnect()

	for o, a in opts:
		if o in ('-g','--settings_save'):
			sr.SaveSettings(settings_path)
		else:
			continue
			
	del sr

	sys.exit(0)