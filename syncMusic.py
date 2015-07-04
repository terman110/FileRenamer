#!/usr/bin/env python
#!/usr/bin/python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from os import listdir, system, chdir, getcwd
from os.path import isfile, join, dirname, realpath, splitext, isdir
import os
import subprocess
import shutil
import getopt
import sys
import time

def main(argv):   
	extns = ['.mp3', '.m4a', '.wav', '.aiff', '.aac', '.alac', '.flac', '.m4p', '.ogg', '.wma']
	s_user = 'Jan'
	s_passwd = 'gkt63q4v'
	s_server = '192.168.178.14'
	s_folder = 'Music'
	s_mount = '/Volumes/Storage/remmusic'

	c_local = False
	c_remote = False

	remote = True

	ddir='/Volumes/Storage/iTunesMusic/Music'

	try:
		opts, args = getopt.getopt(argv,"hd:u:p:s:f:m:rc")# ,["ifile=","ofile="])
	except getopt.GetoptError as err:
		print( '(!) ' + str(err))
		print( ' ')
		print( usage())
		sys.exit(2)
	for o, a in opts:
		if o in ('-h','--help'):
			usage()
			sys.exit()
		elif o in ('-d','--directory'):
			chdir(str(a))
			ddir = str(a)
			print(ddir)
		elif o in ('-u','--user'):
			s_user = str(a)
		elif o in ('-p','--password'):
			s_passwd = str(a)
		elif o in ('-s','--server'):
			s_server = str(a)
		elif o in ('-f','--remotedir'):
			s_folder = str(a)
		elif o in ('-m','--mount'):
			s_mount = str(a)
		elif o in ('-l','--copy2local'):
			c_remote = True
		elif o in ('-r','--copy2remote'):
			c_local = True

	syscom = 'mount_smbfs //' + s_user + ':' + s_passwd + '@' + s_server + '/' + s_folder + ' ' + s_mount

	cwd = dirname( realpath(__file__))
	print(cwd)
	if len(ddir)==0:
		ddir = cwd

	print( '( ) Working directory: "' + ddir + '"')

	lff=[];
	for path, subdirs, files in os.walk(ddir):
		for name in files:
			f = os.path.join(path, name)
			if os.path.isfile(f) and f[len(f)-4:].lower() in extns:
				ff = f.replace( ddir, '')
				lff.append(ff)

	if len(files) < 1:
		print( '  (!) Directory doesn\'t contain any suiting files ...')
		exit(-1)

	rff=[];
	print( '( ) Create mount point ...')
	s_mp = 'mkdir ' + s_mount
	s_mp.replace('./','')
	system( s_mp)
	
	print( '( ) Connect to server ...')
	if system(syscom) is not 0:
		print( '  (!) Unable to mount remote server ...')
		s_mp = 'rm -r ' + s_mount
		system( s_mp)
		exit(-2)
	else:
		for path, subdirs, files in os.walk(s_mount):
			for name in files:
				f = os.path.join(path, name)
				if os.path.isfile(f) and f[len(f)-4:].lower() in extns:
					ff = f.replace( ddir, '')
		 			rff.append(ff)

	# rff=list(lff)
	# rff.pop(100)

	if c_local:
		print( '(-) Copy local files to remote ...')
		for i in range(len(lff)):
			ff = lff[i]
			if ff not in rff:
				dd=os.path.dirname(ff)
				rd=s_mount+dd
				if not os.path.isdir(rd):
					print('  (r) Make directory "'+dd+'" on remote ...')
					os.makedirs(rd)
				scrf = ddir+ff 
				dstf = s_mount+ff
				print('  (R) Copy "'+os.path.basename(ff)+'" to remote ...')
				shutil.copy( scrf, dstf)
				rff.append(ff)

	if c_remote:
		print( '(-) Copy remote files to local ...')
		for i in range(len(rff)):
			ff = rff[i]
			if ff not in rff:
				dd=os.path.dirname(ff)
				rd=ddir+dd
				print('  (l) Create directory "'+dd+'" on local ...')
				os.makedirs(rd)
				scrf = s_mount+ff 
				dstf = ddir+ff
				print('  (L) Copy "'+os.path.basename(ff)+'" to local ...')
				shutil.copy( scrf, dstf)
				lff.append(ff)

	print( '( ) Finishing up ...')
	if remote:
		s_mp = 'umount ' + s_mount
		system(s_mp)
		s_mp = 'rm -r ' + s_mount
		system(s_mp)

def substr( s, begin, length):
	return s[ begin : begin + length]

def usage():
	print( ' ')
	print( ' ')
	print( 'syncMusic 0.1 by dev@lightgraffiti.de')
	print( '---------------------------------------')
	print( 'Synchronize two folders, preferable music files.')
	print( ' ')
	print( 'Usage: ')
	print( ' ')
	print( '   showRenamer.py -h -d <directory> -s <remote server> -u <user> -p <password> -f <remote directory> -m <mount point>')
	print( ' ')
	print( '-h [--help]                         Show this help')
	print( '-r [--copy2remote]                  Copy files from local to remote machine')
	print( '-l [--copy2local]                   Copy files from remote to local machine')
	print( '-d [--directory] <directory>        Source directory on local machine, other than current')
	print( '-s [--server] <remote server>       Server address')
	print( '-u [--user] <user>                  Server username')
	print( '-p [--password] <password>          Server password')
	print( '-f [--remotedir] <remote directory> Directory on server')
	print( '-m [--mount] <mount point>          Mount point (directory) on local machine')
	print( ' ')
	print( ' ')

if __name__ == "__main__":
	print(time.ctime())
	main(sys.argv[1:])
