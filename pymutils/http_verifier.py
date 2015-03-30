import time
import requests
from requests import exceptions as reqexcept
from .verifier import Verifier
from .global_storage import Globals

class HttpOkVerifier(Verifier):
	def __init__(self, **kwargs):
		self.url = ""
		self.timeout = 30
		self.interval = 1
		self.headers = {}

		if "url" in kwargs:
			self.url = kwargs["url"]

		if "timeout" in kwargs:
			self.timeout = kwars["timeout"]

		if "interval" in kwargs:
			self.interval = kwargs["interval"]

		if "headers" in kwargs:
			self.headers = kwargs["headers"]

	def run(self, proc):
		passed = False
		timeout_at = time.time() + self.timeout
		while not passed and time.time() < timeout_at:
			try:
				self.log_verbose("Attempting connection to {0} with a timeout of {1}s".format(self.url, self.interval))
				resp = requests.get(self.url, headers=self.headers, timeout=self.interval)
				if resp.status_code >= 200 and resp.status_code < 300:
					passed = True
				else:
					self.log_fail("Got status {0} from server.".format(resp.status_code))
			except reqexcept.ConnectionError as e:
				self.log_fail("Connection error: {0}".format(e))
				pass
			if Globals.shutdown:
				return False
		return passed
