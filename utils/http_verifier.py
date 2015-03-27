import time
import requests
from requests import exceptions as reqexcept
from .verifier import Verifier

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
				resp = requests.get(self.url, headers=self.headers, timeout=self.interval)
				if resp.status_code >= 200 and resp.status_code < 300:
					passed = True
			except reqexcept.ConnectionError:
				pass
		return passed
