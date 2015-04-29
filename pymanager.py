from pymutils.process import Process
import pymutils.verifier as verifier
from optparse import OptionParser
import pymutils.http_service as http_service
from pymutils.debug import verbose, debug
import collections
import os
import json
import inspect
import signal
import sys
import time
from pymutils.global_storage import Globals

version = "0.2.5"
__version__ = version

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
			Globals.status = "force shutdown"
			for proc in Process.processes:
				if proc.poll() is None:
					proc.kill()
			Globals.may_terminate = True
		return
	print("Shutting down gracefully (SIGINT again to terminate immediately)...")
	Globals.shutdown = True
	Globals.status = "shutdown"
	for proc in Process.processes:
		if Globals.in_force_quit:
			return
		try:
			if proc.poll() is None:
				proc.force_terminate(Globals.terminate_time_allowed)
		except Exception:
			pass
	Globals.may_terminate = True

def spawnDaemon(func, conf):
    try: 
        pid = os.fork() 
        if pid > 0:
            return
    except OSError as e:
        print("fork #1 failed: {0} ({1})".format(e.errno, e.strerror))
        sys.exit(6)

    os.setsid()

    try: 
        pid = os.fork() 
        if pid > 0:
            sys.exit(0) 
    except OSError as e: 
        print("fork #2 failed: {0} ({1})".format(e.errno, e.strerror))
        sys.exit(7)

    func(conf)

    os._exit(os.EX_OK)

def main():
	parser = OptionParser()
	parser.add_option("-V", "--version", dest="version", default=False, action="store_true", help="Display version and exit.")
	parser.add_option("-v", "--verbose", dest="verbose", default=False, action="store_true", help="Display process launch and verification step-by-step.")
	parser.add_option("-w", "--debug", dest="debug", default=False, action="store_true", help="Display debug information. Implies verbose.")
	parser.add_option("-f", "--file", dest="filename", default="pymanager.json", help="The name of the pymanager file to use, defaults to pymanager.json.", metavar="FILE")
	parser.add_option("-d", "--daemon", dest="daemon", default=False, action="store_true", help="Daemonize self after processes are launched.")
	opts, args = parser.parse_args()

	if opts.version:
		print("pymanager version {0}".format(version))
		exit(0)

	config = parse(opts.filename)
	if opts.debug:
		config["verbose"] = 2
	elif opts.verbose:
		config["verbose"] = 1
	else:
		config["verbose"] = 0

	if opts.daemon:
		spawnDaemon(spawn_and_monitor, config)
		return 0
	else:
		return spawn_and_monitor(config)

def spawn_and_monitor(config):
	verifiers = {}

	if "verbose" in config:
		Globals.verbose = config["verbose"]

	verbose("Checking HTTP configuration.")
	if "http" in config:
		hconf = config["http"]
		debug("HTTP is present.")
		if "enabled" in hconf and hconf["enabled"]:
			debug("HTTP is enabled.")
			port = 5001
			if "port" in hconf:
				debug("Port is present in configuration.")
				port = hconf["port"]
			http_service.fork_http_service(port)
			verbose("HTTP service listening on port :{0}".format(port))
		else:
			debug("HTTP is disabled.")

	if "default_shell" in config:
		debug("Default shell is present, value: {0}".format(config["default_shell"]))
		Globals.default_shell = config["default_shell"]

	verbose("Parsing modules list.")
	Globals.status = "parsing modules"
	if "modules" in config:
		for module, definition in config["modules"].items():
			debug("Loading module {0}".format(module))
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
									debug("Loading verifier {0}".format(v))
									verifiers["{0}.{1}".format(module, v)] = getattr(mod, v)
								else:
									print("Warning: object '{0}' from module {1} is not a subclass of Verifier".format(v, module))
							else:
								print("Warning: object '{0}' from module {1} is not a class".format(v, module))
						except AttributeError:
							print("Warning: missing verifier '{0}' from module {1}".format(v, module))
				except ImportError:
					print("Warning: module {0} not found.".format(module))

	verbose("Modules are loaded, parsing processes.")
	if not "processes" in config:
		print("Error: No processes listed in the configuration file.")
		return 4

	signal.signal(signal.SIGINT, graceful_shutdown)
	signal.signal(signal.SIGTERM, graceful_shutdown)
	signal.signal(signal.SIGQUIT, graceful_shutdown)

	verbose("Processes parsed, launching.")
	Globals.status = "launching processes"
	if "messages" in config:
		Globals.messages = config["messages"]

	try:
		for key, procdef in config["processes"].items():
			verbose("Launching process key '{0}'.".format(key))
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
				debug("Setting up verifier {0} for process.".format(procdef["verifier"]["type"]))
				vfy = verifiers[procdef["verifier"]["type"]](**args)
			options = {}
			if "options" in procdef:
				options = procdef["options"]
			verbose("Creating process.")
			proc = Process(cmdargs, vfy, **options)
			Process.add_process(proc)
			verbose("Process creation finished.")
	except Exception as e:
		etype, _, _ = sys.exc_info()
		print("Error: could not set up processes: {0}: {1}".format(etype.__name__, e))
		Globals.status = "shutdown"
		#traceback.print_exc()
		for proc in Process.processes:
			try:
				proc.kill()
			except Exception:
				pass
			return 5

	verbose("Finished setting up processes.")
	if "keep_alive" in config:
		if config["keep_alive"]:
			Globals.keep_alive = True

	if "graceful_time" in config:
		try:
			t = int(config["graceful_time"])
			if t < 0:
				raise ValueError
			Globals.terminate_time_allowed = t
		except ValueError:
			print("Warning: invalid graceful_time '{0}', must be a positive number.".format(t))

	
	Globals.status = "running"
	runningProcesses = len(Process.processes)
	while (runningProcesses or Globals.keep_alive) and not Globals.shutdown:
		runningProcesses = 0
		for proc in Process.processes:
			result = proc.poll()
			if result is None:
				runningProcesses += 1
		time.sleep(5)
		if not Globals.keep_alive and not runningProcesses:
			Globals.may_terminate = True

	verbose("Entering shutdown phase.")
	Globals.status = "shutdown"
	while not Globals.may_terminate:
		time.sleep(5)

	return 0

if __name__ == "__main__":
	exit(main())