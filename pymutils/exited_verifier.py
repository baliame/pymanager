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
			self.log_fail("Process did not exit in given timeframe {0}s".format(self.timeout))
			return False
		if proc.code() != self.expect_code:
			self.log_fail("Expected exit code {0}, got {1}".format(proc.code(), self.expect_code))
		return proc.code() == self.expect_code