import shlex
import subprocess

class UninitializedException(Exception):
	def __init__(self, process):
		self.commandLine = process.commandLine

	def __str__(self):
		return "Process is not initialized.\nCommand line for process: {0}".format(self.commandLine)

class TerminatedException(Exception):
	def __init__(self, process):
		self.commandLine = process.commandLine
		self.code = process.proc.returncode

	def __str__(self):
		return "Process is not initialized.\nCommand line for process: {0}\nExit code: {1}".format(self.commandLine, self.code)

class VerificationFailedException(Exception):
	def __init__(self, process):
		self.commandLine = process.commandLine

	def __str__(self):
		return "Process verification failed.\nCommand line for process: {0}".format(self.commandLine)

class Process:
	processes = []
	next_id = 1

	@classmethod
	def add_process(self, proc):
		Process.processes.append(proc)

	def __init__(self, commandLine, verifier=None, **kwargs):
		self.internalId = Process.next_id
		Process.next_id += 1
		self.init(commandLine, verifier, **kwargs)
	
	def init(self, commandLine, verifier=None, **kwargs):
		self.commandLine = commandLine
		if isinstance(commandLine, list):
			self.cmdString = " ".join(commandLine)
			args = commandLine
		else:
			self.cmdString = commandLine
			args = shlex.split(commandLine)
		print("$ {0}".format(self.cmdString))
		out_method = None
		if "suppress_output" in kwargs and kwargs["suppress_output"]:
			if "redirect_output" in kwargs:
				raise ArgumentError("Suppress output and redirect output are mutually exclusive.")
			out_method = subprocess.PIPE
		elif "redirect_output" in kwargs:
			out_method = open(kwargs["redirect_output"], 'w')
		cwd = None
		if "working_directory" in kwargs:
			cwd = kwargs["working_directory"]
		self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=out_method, stderr=subprocess.STDOUT, cwd=cwd)
		self.verifier = verifier
		self.options = kwargs
		if verifier is not None:
			if not verifier.run(self):
				raise VerificationFailedException(self)
		self.rcode = None

	def __del__(self):
		if hasattr(self, "proc") and self.proc is not None:
			self.proc.poll()
			if self.proc.returncode is None:
				self.force_terminate()

	def restart(self, timeout=10):
		if hasattr(self, "proc") and self.proc is not None:
			if self.proc.poll() is None:
				self.force_terminate(timeout)
			if self.proc.stdin:
				self.proc.stdin.close()
			if self.proc.stdout:
				self.proc.stdout.close()
		self.init(self.commandLine, self.verifier, **self.options)

	def wait(self, timeout=None):
		if hasattr(self, "proc") and self.proc is not None:
			code = self.proc.wait(timeout)
			self.rcode = code
			return code
		else:
			raise UninitializedException(self)

	def write(self, stdin):
		if hasattr(self, "proc") and self.proc is not None and self.proc.stdin is not None:
			self.proc.stdin.write(stdin)
		else:
			raise UninitializedException(self)

	def code(self, blocking=True, timeout=None):
		if hasattr(self, "proc") and self.proc is not None:
			code = self.proc.poll()
			if code is None and blocking:
				try:
					self.proc.wait(timeout)
				except subprocess.TimeoutExpired:
					return None
			else:
				self.rcode = code
				return code
		else:
			raise UninitializedException(self)

	def poll(self):
		if not hasattr(self, "proc") or self.proc is None:
			raise UninitializedException(self)
		self.proc.poll()
		self.rcode = self.proc.returncode
		return self.proc.returncode

	def signal(self, signal):
		if hasattr(self, "proc") and self.proc is not None and self.proc.returncode is None:
			self.proc.send_signal(signal)
		elif hasattr(self, "proc") and self.proc is not None:
			raise TerminatedException(self)
		else:
			raise UninitializedException(self)

	def pid(self):
		if hasattr(self, "proc") and self.proc is not None:
			return self.proc.pid
		else:
			raise UninitializedException(self)


	def terminate(self):
		if hasattr(self, "proc") and self.proc is not None:
			self.proc.terminate()
		else:
			raise UninitializedException(self)

	def kill(self):
		if hasattr(self, "proc") and self.proc is not None:
			self.proc.kill()
		else:
			raise UninitializedException(self)

	def force_terminate(self, timeout=10):
		if hasattr(self, "proc") and self.proc is not None:
			self.terminate()
			try:
				self.wait()
			except subprocess.TimeoutExpired:
				self.kill()
		else:
			raise UninitializedException(self)

	def status_string(self):
		if hasattr(self, "proc") and self.proc is not None:
			if self.proc.poll() is None:
				return "running"
			else:
				return "terminated"
		else:
			raise UninitializedException(self)

	def pid(self):
		if hasattr(self, "proc") and self.proc is not None:
			if self.proc.poll() is not None:
				raise TerminatedException(self)
			else:
				return self.proc.pid
		else:
			raise UninitializedException(self)

	def get_data(self):
		procdata = {
			"id": self.internalId,
			"command": self.cmdString,
			"status": self.status_string()
		}
		if procdata["status"] == "running":
			procdata["pid"] = self.pid()
		else:
			procdata["code"] = self.code(False)
		return procdata