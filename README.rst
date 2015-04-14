Process manager in Python
=========================
Launches and manages processes according to a set of specifications, shuts them down in bulk on request.
Useful for test environments without inherent cleanup.

Usage
-----
To use, place a configuration file in the target directory. The configuration file is a json file (by default, pymanager.json, but it can be changed with the -f or --file switch) following a specified structure.

You may also launch the process manager as a daemon. Pass the -d or --daemon switch to do this.

Concepts
--------
The manager works with two kinds of objects: processes and verifiers.

A single process is an entry which is launched by the manager. The amount of processes cannot currently be changed during execution, however, any process may be restarted at will. Currently, this manipulation can only be done via the exposed HTTP interface, but a command line tool with persistence is planned.

A verifier is an instance of a Verifier object that may be attached to processes. The goal of verifiers is to check if the process managed to achieve a desired state - for example, in a testing environment of an HTTP service, testing cannot proceed until the service starts its listening process. In other scenarios, a certain process may be required to finish running and exit with a 0 status code before another process may be ran.

There are two verifiers built into the manager, the HttpOkVerifier from the http_verifier module, which verifies by periodically querying a specified URL and passes if a 200 OK is returned; and the ExitedVerifier from the exited_verifier module, which passes if the attached process exits with the provided status code within the given timeframe.

Additional verifiers may be loaded through the modules directive in the configuration file. The only requirement is that all verifier classes must extend the Verifier base class provided by pymanager.

Configuration
-------------
Below is the expected structure of a pymanager file.

.. code-block:: json

    {
      "modules": {
        "pymutils.http_verifier": {
          "verifiers": ["HttpOkVerifier"]
        }
      },
      "http": {
        "enabled": true,
        "port": 5001
      },
      "keep-alive": true,
      "processes": {
        "test": {
          "executable": "python3",
          "arguments": ["test.py", "-v", "-t"],
          "options": {
            "suppress_output": false
          },
          "verifier": {
            "type": "pymutils.http_verifier.HttpOkVerifier",
            "arguments": {
              "url": "http://google.com"
            }
          }
        }
      }
    }

modules
^^^^^^^
All verifiers loaded used must be loaded in the modules section. The key of the verifiers is the import to load (ex. http_verifier), and the list under the key verifiers contains the list of classes to add to the verifier registry.

http
^^^^
The application exposes an HTTP interface for convenient manipulation and data exchange. To flip the switch, add

    "enabled": true

in the HTTP object in the configuration. The port by default is 5001, which may be modified using the `port` option.

The available HTTP endpoints currently are:

    GET /

Lists all processes managed by the application, including the status, the internal ID and the process ID or exit code, which ever applicable.

    GET /status

Returns the state of the application. If the status is 'running', it is safe to assume that all processes are in their desired state.

    POST /restart/<id>

Restarts the process with the internal ID <id>. The application gives a few seconds for the process to gracefully terminate. If the process cannot gracefully terminate within the given timeframe, it is forcibly terminated before starting it up again.

    DELETE /

Shuts down the application asynchronously. The request will return and the graceful termination period will begin. By default, 10 seconds are allowed for each process to terminate gracefully before forceful termination, this time period can be modified though - see below.

keep_alive
^^^^^^^^^^
By default, the pymanager process terminates if all processes are terminated. You can override this behaviour and keep the manager process running by setting keep-alive to true. This is useful if one or more processes can be restarted later without requiring the other processes which are defined.

graceful_time
^^^^^^^^^^^^^
The graceful_time option may be specified to control the amount of time given for each subprocess to terminate gracefully before forceful termination.

default_shell
^^^^^^^^^^^^^
The default_shell option defines the default shell to use for environment file operations and for processes with the 'shell' option set to true. This option defaults to 'true', which is the user default shell.

processes
^^^^^^^^^
Each process is an entry in the list of processes. A process requires an executable and arguments. The executable is, naturally, require and the arguments must be provided even if the process takes no arguments - in that case, as an empty list.

Optionally, options may be passed to the process launcher. Currently recognized options:
* suppress_output, if set to true, the output of the process will not be displayed on standard output. By default, all process output is displayed. Mutually exclusive with suppress_output.
* working_directory; if present, the working directory of the process is modified to the path provided. The path may be relative or absolute. Note that when searching for the executable, this working directory is not considered, and the executable will be searched for relative to the directory where you launched pymanager.
* redirect_output specifies a filename. The file will receive all output generated by the process. Mutually exclusive with suppress_output.
* environment_file specifies a filename. This file will be sourced and the resulting environment will be used as the environment for the process. This is a potentially dangerous operation, use with care.
* shell may be 'true' or the name of a command to run as a shell (eg. bash, sh, zsh, etc.). If shell is simply set to true, the default_shell option from global settings will be used. Shell defaults to false, which means no shell is spawned under the process.

A process may also include a verifier. If the verifier key is present, the type must be provided. The type of the verifier must be loaded in the modules section and takes the form of 'module.classname'. Optionally, you may provide a dictionary of arguments to pass to the keyword arguments of the initializer function of the verifier.

messages
^^^^^^^^
Optionally, a list of message types (strings) may appear in the configuration under the key 'messages'. This controls the verbosity of the output from the application. By default, no additional output is displayed. Currently, the following options are available:

* process.exit - display message when a controlled process exits, along with the return code.
* verifier.fail - display messages about verifier attempts failing.
* verifier.verbose - display all (debug) messages from verifier, implies all other verifier options.

Signal response
===============
The application will respond to SIGINT, SIGTERM and SIGQUIT the same way as if a DELETE / request was issued to its HTTP endpoint.