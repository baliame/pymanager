import subprocess
from .verifier import Verifier

class ExitedVerifier(Verifier):
	def __init__(self, **kwargs):
		self.timeout = 30
		self.expect_code = 0

		if "timeout" in kwargs:
			self.timeout = kwargs["timeout"]

		if "expect_code" in kwargs:
			self.expect_code = kwargs["expect_code"]

	def run(self, proc):
		try:
			proc.wait(self.timeout)
		except subprocess.TimeoutExpired:
			return False
		return proc.returncode == self.expect_code