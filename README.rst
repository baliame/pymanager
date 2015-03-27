Process manager in Python
=========================
Launches and manages processes according to a set of specifications, shuts them down in bulk on request.
Useful for test environments without inherent cleanup.

Usage
-----
To use, place a configuration file in the target directory. The configuration file is a json file (by default, pymanager.json, but it can be changed with the -f or --file switch) following a specified structure.

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
        "http_verifier": {
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
            "type": "http_verifier.HttpOkVerifier",
            "arguments": {
              "url": "http://google.com"
            }
          }
        }
      }
    }

Modules
^^^^^^^
All verifiers loaded used must be loaded in the modules section. The key of the verifiers is the import to load (ex. http_verifier), and the list under the key verifiers contains the list of classes to add to the verifier registry.

Http
^^^^
The application exposes an HTTP interface for convenient manipulation and data exchange. To flip the switch, add `"enabled": true` in the HTTP object in the configuration. The port by default is 5001, which may be modified using the `port` option.

Keep-alive
^^^^^^^^^^
By default, the pymanager process terminates if all processes are terminated. You can override this behaviour and keep the manager process running by setting keep-alive to true. This is useful if one or more processes can be restarted later without requiring the other processes which are defined.

Processes
^^^^^^^^^
Each process is an entry in the list of processes. A process requires an executable and arguments. The executable is, naturally, require and the arguments must be provided even if the process takes no arguments - in that case, as an empty list. Optionally, options may be passed to the process launcher. Currently only one option is recognized: suppress_output, if set to true, the output of the process will not be displayed on standard output. By default, all process output is displayed.

A process may also include a verifier. If the verifier key is present, the type must be provided. The type of the verifier must be loaded in the modules section and takes the form of 'module.classname'. Optionally, you may provide a dictionary of arguments to pass to the keyword arguments of the initializer function of the verifier.