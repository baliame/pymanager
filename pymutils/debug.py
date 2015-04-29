from .global_storage import Globals

def debug(message):
	if Globals.verbose >= 2:
		print("[DEBUG] {0}".format(message))

def verbose(message):
	if Globals.verbose >= 1:
		print(message)