from .global_storage import Globals

class Verifier:
	def run(self, proc):
		return True

	def log_fail(self, message):
		if "verifier.fail" in Globals.messages or "verifier.verbose" in Globals.messages:
			print("Verifier fail: {0}".format(message))

	def log_verbose(self, message):
		if "verifier.verbose" in Globals.messages:
			print("Verifier: {0}".format(message))