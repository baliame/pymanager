from bottle import get, post, delete, request, run, abort, HTTPResponse
from .process import Process
from .global_storage import Globals
from threading import Thread
import json

def r403(message):
	raise HTTPResponse(json.dumps({"success": False, "error": {"message": message}}), 403)

def r404(message):
	raise HTTPResponse(json.dumps({"success": False, "error": {"message": message}}), 404)

def r400(message):
	raise HTTPResponse(json.dumps({"success": False, "error": {"message": message}}), 400)

def fork_http_service(port=5001):
	p = Thread(target=launch_http_service, args=(port,))
	p.daemon = True
	p.start()

def launch_http_service(port=5001):
	run(host='localhost', port=port, debug=True, quiet=True)

def async_shutdown():
	for proc in Process.processes:
		if proc.poll() is None:
			proc.force_terminate(Globals.terminate_time_allowed)
	Globals.may_terminate = True

@get("/")
def list_processes():
	if Globals.shutdown:
		r403("Process is in shutdown.")
	output = {
		"count": len(Process.processes),
		"processes": [],
	}
	for proc in Process.processes:
		procdata = proc.get_data()
		output["processes"].append(procdata)
	return output

@post("/restart/<id>")
def restart_process(id):
	if Globals.shutdown:
		r403("Process is in shutdown.")
	p = None
	try:
		for proc in Process.processes:
			if proc.internalId == int(id):
				proc.restart(5)
				data = proc.get_data()
				return {"success": True, "process": data}
		r404("Process with id '{0}' not found.")
	except ValueError:
		r400("Invalid ID '{0}'.".format(id))

@delete("/")
def kill_process_tree():
	if Globals.shutdown:
		r403("Process is in shutdown.")
	Globals.shutdown = True
	p = Thread(target=async_shutdown, args=())
	p.start()
	return {"success": True}

