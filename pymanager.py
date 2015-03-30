import traceback
from pymutils.process import Process
import pymutils.verifier as verifier
from optparse import OptionParser
import pymutils.http_service as http_service
import collections
import os
import json
import inspect
import signal
import sys
import time
from pymutils.global_storage import Globals

def parse(filename):
	try:
		with open(filename, 'r') as f:
			config_data = f.read()
	except FileNotFoundError:
		print("Cannot find file {0}.".format(filename))
		exit(1)
	except Exception as e:
		print("Error while loading file {0}: {1}.".format(filename, e))
		exit(2)
	try:
		jdata = json.JSONDecoder(object_pairs_hook=collections.OrderedDict).decode(config_data)
	except ValueError:
		print("{0} is not a valid JSON file.".format(filename))
		exit(3)

	return jdata

def graceful_shutdown(signum, frame):
	if Globals.in_force_quit:
		return
	if Globals.shutdown:
		if signum == signal.SIGINT:
			Globals.in_force_quit = True
			for proc in Process.processes:
				if proc.poll() is None:
					proc.kill()
			Globals.may_terminate = True
		return
	print("Shutting down gracefully (SIGINT again to terminate immediately)...")
	Globals.shutdown = True
	for proc in Process.processes:
		if Globals.in_force_quit:
			return
		try:
			if proc.poll() is None:
				proc.force_terminate(Globals.terminate_time_allowed)
		except Exception:
			pass
	Globals.may_terminate = True

def main():
	parser = OptionParser()
	parser.add_option("-f", "--file", dest="filename", default="pymanager.json", help="The name of the pymanager file to use, defaults to pymanager.json.", metavar="FILE")
	opts, args = parser.parse_args()
	config = parse(opts.filename)
	verifiers = {}
	if "modules" in config:
		for module, definition in config["modules"].items():
			if "verifiers" not in definition:
				print("Warning: module {0} does not contain a list of verifiers to load.".format(module))
			else:
				try:
					mod = __import__(module)
					for v in definition["verifiers"]:
						try:
							a = getattr(mod, v)
							if inspect.isclass(a):
								if issubclass(a, verifier.Verifier):
									verifiers["{0}.{1}".format(module, v)] = getattr(mod, v)
								else:
									print("Warning: object '{0}' from module {1} is not a subclass of Verifier".format(v, module))
							else:
								print("Warning: object '{0}' from module {1} is not a class".format(v, module))
						except AttributeError:
							print("Warning: missing verifier '{0}' from module {1}".format(v, module))
				except ImportError:
					print("Warning: module {0} not found.".format(module))

	if not "processes" in config:
		print("Error: No processes listed in the configuration file.")
		return 4

	signal.signal(signal.SIGINT, graceful_shutdown)
	signal.signal(signal.SIGTERM, graceful_shutdown)
	signal.signal(signal.SIGQUIT, graceful_shutdown)

	if "messages" in config:
		Globals.messages = config["messages"]

	try:
		for key, procdef in config["processes"].items():
			if "executable" not in procdef or "arguments" not in procdef:
				raise KeyError("Missing executable or arguments in definition for process {0}.".format(key))
			cmdargs = [procdef["executable"]]
			cmdargs += procdef["arguments"]
			vfy = None
			if "verifier" in procdef:
				if "type" not in procdef["verifier"]:
					raise KeyError("Missing verifier type for verifier of process {0}.".format(key))
				if procdef["verifier"]["type"] not in verifiers:
					raise ValueError("Missing verifier {0} used in process {1}".format(procdef["verifier"]["type"], key))
				args = {}
				if "arguments" in procdef["verifier"]:
					args = procdef["verifier"]["arguments"]
				vfy = verifiers[procdef["verifier"]["type"]](**args)

			options = {}
			if "options" in procdef:
				options = procdef["options"]
			proc = Process(cmdargs, vfy, **options)
			Process.add_process(proc)
	except Exception as e:
		etype, _, _ = sys.exc_info()
		print("Error: could not set up processes: {0}: {1}".format(etype.__name__, e))
		#traceback.print_exc()
		for proc in Process.processes:
			try:
				proc.kill()
			except Exception:
				pass

	if "http" in config:
		hconf = config["http"]
		if "enabled" in hconf and hconf["enabled"]:
			port = 5001
			if "port" in hconf:
				port = hconf["port"]
			http_service.fork_http_service(port)

	keepAlive = False
	if "keep_alive" in config:
		if config["keep_alive"]:
			keepAlive = True

	if "graceful_time" in config:
		try:
			t = int(config["graceful_time"])
			if t < 0:
				raise ValueError
			Globals.terminate_time_allowed = t
		except ValueError:
			print("Warning: invalid graceful_time '{0}', must be a positive number.".format(t))

	runningProcesses = len(Process.processes)
	while (runningProcesses or keepAlive) and not Globals.shutdown:
		runningProcesses = 0
		for proc in Process.processes:
			result = proc.poll()
			if result is None:
				runningProcesses += 1
		time.sleep(5)
		if not keepAlive and not runningProcesses:
			Globals.may_terminate = True

	while not Globals.may_terminate:
		time.sleep(5)

	return 0

if __name__ == "__main__":
	exit(main())