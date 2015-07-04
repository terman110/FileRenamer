#!/usr/bin/env python
#!/usr/bin/python

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from os import listdir, system, chdir, getcwd, makedirs
from os.path import isfile, join, dirname, realpath, splitext, isdir, exists
from types import ListType
import itertools as it
#import subprocess
import shutil
import getopt
import sys
import select

from mutagen.mp3 import EasyMP3 as MP3

def fileSafe(path):
	# return str( [c for c in path if c.isalpha() or c.isdigit() or c==' ']).rstrip()
	keepcharacters = (' ','.','_','/','\\')
	return "".join(c for c in path if c.isalnum() or c in keepcharacters ).rstrip()

# Check if s is a number
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        from unicodedata import numeric
        numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
	return False

# Is s an integer?
def is_integer(s):
    try:
        int(s)
        return True
    except ValueError:
        pass
 
    try:
        from unicodedata import numeric
        numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
	return False

# Read from console with timeout
def input( question, timeout = 120):
	question += " (" + str(timeout) + "s): "
	sys.stdout.write( question)
	sys.stdout.flush()
	i, o, e = select.select( [sys.stdin], [], [], timeout )

	if (i):
		return sys.stdin.readline().strip()
	else:
		print('')
		return False

# Read from console with timeout and return default after timeout
def inputDef( question, deflt, timeout = 120):
	re = input( question, timeout)
	if not re:
		print( deflt)
		return deflt
	else:
		return re

# Read integer from console
def inputInt( question):
	while(True):
		question += ": "
		sys.stdout.write( question)
		sys.stdout.flush()
		i, o, e = select.select( [sys.stdin], [], [] )

		if i:
			tmp = sys.stdin.readline().strip()
			if is_integer( tmp):
				return int( tmp)
			else:
				print('')

# Unicode to ASCII string
def toStr( string):
	if type(string) is ListType:
		string = string[0]
	return unicode( string).decode('ascii','replace')

# Check if file has extension
def hasExt( _file, _ext):
	if _ext[0] is not '.':
		_ext = '.' + _ext
	fileName, fileExtension = splitext(_file)
	return fileExtension == _ext

# List dirs
def listDirs( _dir):
	return [ f for f in listdir(_dir) if isdir(join(_dir,f))]

# List files
def listFiles( _dir):
	return [ f for f in listdir(_dir) if isfile(join(_dir,f))]

# Filter directories for file types
def filterDirs( _dir, _dirs, _ext):
	dd = []
	for d in _dirs:
		if d[0] == '.':
			continue

		# Join for absolute path
		cd = join(_dir,d)

		# Add recursive directories
		cds = listDirs( cd)
		if len( cds) > 0:
			for ccds in cds:
				if ccds[0] == '.':
					continue
				_dirs.append( join(cd,ccds))

		# Filter folders that don't contain at least one file with _ext
		cf = listFiles( cd)
		if len( cf) < 1:
			continue

		# Compare file extensions in dir 
		__hasExt = False
		for f in cf:
			if hasExt( f, _ext):
				__hasExt = True
				break
		if not __hasExt:
			continue

		# Append survivors to list
		dd.append( join(_dir,d))
	return dd

# Filter files for file types
def filterFiles( _dir, _files, _ext):
	ff = []
	for f in _files:
		if f[0] == '.':
			continue
		f = join( _dir, f)
		if not isfile( f) or not hasExt( f, _ext):
			continue
		ff.append( f)
	return ff

# Read one tag from MP3
def readTag( _tag, _key):
	try:
		s = toStr( _tag[str(_key)])
		while s[0] == " " or s[0] == "\t" or s[0] == "\r" or s[0] == "\n":
			s = s[1:]
		while s[-1] == " " or s[-1] == "\t" or s[-1] == "\r" or s[-1] == "\n":
			s = s[:-1]
		return s
	except:
		return str("")

# Read meta of one MP3 file
def readMeta( _tag, _path = ''):
	return {
		'title': 		readTag( _tag, "title"),
		'tracknumber':	readTag( _tag, "tracknumber"),
		'artist': 		readTag( _tag, "artist"),
		'album': 		readTag( _tag, "album"),
		'date': 		readTag( _tag, "date"),
		'genre': 		readTag( _tag, "genre"),
		'handle':		_tag,
		'file':			_path
	}

# Read meta data of all MP3 files
def readMP3( _files):
	meta = []
	for f in _files:
		if not exists( f):
			print( '(!) The file "' + f + '" does not exist')
		_tag = MP3( f)
		meta.append( readMeta( _tag, f))
	return meta

# Get all elements in list wihout duplicates
def diffList( _list):
	t2 = _list[1:]
	t2.append("")
	return [a for (a,b) in zip(_list, t2) if not a==b]

# Extract values from list of dictionaries with the key _key
def extractValueOfAlbumData( _meta, _key):
	value = diffList( [x[str(_key)] for x in _meta])
	if len( value) > 1:
		value = inputDef( "  (?) Enter value for '" + _key + "' ['" + "' or '".join(value) + "'']", value[0])
		if not value or len(value) < 1:
			value = value[0]
	elif len( value) < 1:
		value = input( "  (?) Enter value for '" + _key + "'")
		if not value:
			raise NameError('No value entered')
	else:
		value = value[0]
	return value

def usage():
	print( 'Usage: ')
	print( ' ')
	print( '   songRenamer.py -h -c -s <source_directory> -t <target_directory>')
	print( ' ')
	print( '-h [--help]                         Show this help')
	print( '-s [--source] <directory>        	Parent source directory. Must exist.')
	print( '-t [--target] <directory>        	Parent target directory')
	print( '-c [--cleanup]                      Delete old directories including remaining file')
	print( ' ')
	print( ' ')

def main(argv):   
	print( ' ')
	print( ' ')
	print( 'songRenamer 0.1 by dev@lightgraffiti.de')
	print( '---------------------------------------')
	print( 'Rename and move mp3 files the iTunes style')
	print( 'It depends heavily on mutagen <https://bitbucket.org/lazka/mutagen>')
	print( ' ')

	_delete = False		# Delete old dir?
	_ext = 'mp3'		# File extension

	# Set working directory
	try:
		_cwd = dirname( realpath(__file__))
		_dir = _cwd
		
		''' DEBUG '''
		_dir = join( _cwd, "test")

		# Target working directory
		_twd = _dir

		print( '(i) Working directory: "' + _dir + '"')
		print( '(i) Target directory: "' + _twd + '"')
	except:
		print( '(!) Working or target directory init failed')
		return(-1)

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
		elif o in ('-s','--source'):
			_dir = fileSafe( str(a))
			if not isdir( _dir) or not exists( _dir):
				print( 'Source directory path is not valid')
				sys.exit()
		elif o in ('-t','--target'):
			_twd = fileSafe( str(a))
		elif o in ('-c','--cleanup'):
			_delete = True

	try:
		print( '(i) Source directory: "' + _dir + '"')
		print( '(i) Target directory: "' + _twd + '"')
	except:
		print( '(!) Reading working or target directory failed')
		return(-1)

	# Get directories that contain mp3 files
	_dirs = filterDirs( _dir, listDirs( _dir), _ext)

	if len(_dirs) < 1:
		print( '(!) No music directories found ...')
		exit(-1)

	# Loop all music dirs
	print( '  (+) Extracting meta data')
	for d in _dirs:
		try:
			print( '  (i) Current directory: "' + d + '"')
		except:
			print( '  (i) Current directory...')

		# Get all mp3 files
		_files = filterFiles( d, listFiles( d), _ext)

		# Loop all music files
		# meta -> 'title', 'tracknumber', 'artist', 'album', 'date', 'genre', 'handle', 'file'
		meta = readMP3( _files)
		try:
			artist = extractValueOfAlbumData( meta, "artist")
			print( '  (-) Artist: ', artist)
		except:
			print( '  (!) Could not retrieve artist name\n  (!) Skipping folder')
			continue

		try:
			album = extractValueOfAlbumData( meta, "album")
			print( '  (-) Album: ', album)
		except:
			print( '  (!) Could not retrieve album name\n  (!) Skipping folder')
			continue

		try:
			date = extractValueOfAlbumData( meta, "date")
			print( '  (-) Date: ', date)
		except:
			date = ''

		try:
			genre = extractValueOfAlbumData( meta, "genre")
			print( '  (-) Genre: ', genre)
		except:
			genre = ''

		tnbs = []
		try:
			for tn in [x["tracknumber"] for x in meta]:
				if not is_number( tn):
					raise
				tnbs.append( int( tn))

			if not min( tnbs) == 1 or not max( tnbs) == len(meta):
				tnbs = []
				raise

			for t in range( 1, len(meta)+1):
				if not t in tnbs:
					tnbs = []
					raise
		except:
			print( '  (?) Tracknumbers are faulty and must be entered by user')
			tnbs = []

		# Prepare file sytem
		print( '  (+) Preparing file system')
		_ctd = fileSafe( join( join( _twd, artist), album))
		print( '      (+) Target dir is "' + _ctd + '"')
		try:
			makedirs( _ctd)
		except:
			print( '      (!) Failed to create folder\n      (!) Trying it anyway')

		# Writing meta data
		print( '  (+) Writing meta data')
		for i in range( len(meta)):
			meta[i]['artist'] = artist
			meta[i]['handle']['artist'] = meta[i]['artist']

			meta[i]['album'] = album
			meta[i]['handle']['album'] = meta[i]['album']
			
			meta[i]['date'] = date
			meta[i]['handle']['date'] = meta[i]['date']

			meta[i]['genre'] = genre
			meta[i]['handle']['genre'] = meta[i]['genre']
			
			if meta[i]['title'] and len(meta[i]['title']) > 0:
				meta[i]['title'] = meta[i]['title'].title()
			else:
				meta[i]['title'] = input( '  (?) Enter trackname for "' + meta[i]['file'] + '"').title()
			meta[i]['handle']['title'] = meta[i]['title']

			if tnbs and len( tnbs) == len( meta):
				meta[i]['tracknumber'] = str( tnbs[i])
			else:
				print("  (!) Track number faulty")
				meta[i]['tracknumber'] = str( inputInt('  (?) Enter tracknumber for "' + meta[i]['file'] + '"'))
			meta[i]['handle']['tracknumber'] = meta[i]['tracknumber']

			meta[i]['handle']['copyright'] = ""
			meta[i]['handle']['organization'] = ""
			meta[i]['handle']['website'] = ""
			# meta[i]['handle']['performer'] = ""
			# meta[i]['handle']['composer'] = ""
			# meta[i]['handle']['conductor'] = ""
			# meta[i]['handle']['discnumber'] = "1"

			#print( meta[i]['handle'].pprint())
			meta[i]['handle'].save()

			print( "      -> " + meta[i]['artist'] + " - " + meta[i]['album'] + " - " + meta[i]['tracknumber'].zfill(2) + " - " + meta[i]['title'])
			if not _ext[0] == '.':
				_ext = '.' + _ext
			fn = fileSafe( meta[i]['tracknumber'].zfill(2) + " " + meta[i]['title'] + _ext)
			
			newfn = join( _ctd, fn)
			try:
				shutil.move( meta[i]['file'], newfn)
			except (IOError, os.error) as why:
				print( str(why))
			except Error as err:
				print(err.args[0])
			except:
				print("      (!) Unable to move file!")
				print('           From')
				print('            "' + meta[i]['file'] + '"')
				print('           to')
				print('            "' + newfn + '"')
				_delete = False

		if _delete and not d == _ctd:
			shutil.rmtree( d)

		# print( meta[0]['file'])
		# print( meta)

		#inputDef("Enter","avc",3)

		# for i in range( len(meta)):
		# 	meta[i]['handle'].save()

		#text=u"An example"
		#print _tag.pprint()
		#print _tag.info.length, _tag.info.bitrate

if __name__ == "__main__":
	main(sys.argv[1:])