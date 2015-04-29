from .global_storage import Globals
import sys

def tofileln(message):
	if Globals.outfile is None:
		Globals.outfile = sys.stdout
	if Globals.outfile is sys.stdout:
		print(message, file=sys.stdout)
	else:
		b = "{0}\n".format(message).encode('utf-8')
		Globals.outfile.write(b)

def debug(message):
	if Globals.verbose >= 2:
		tofileln("[DEBUG] {0}".format(message))

def verbose(message):
	if Globals.verbose >= 1:
		tofileln("[INFO] {0}".format(message))

def log(message):
	tofileln(message)