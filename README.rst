Notes:
------

Sadly, there's no way to rename git repositories. There was a name conflict between this module and the mozilla services bipostal module. I've had to recreate this as a separate entity. Original author is https://github.com/jbalogh/bipostal

Getting Started
---------------

1. Make your virtualenv.
2. Install the python packages::

    pip install -r dev-reqs.txt

2.5 You will need to manually install the Mozilla Services library

    cd deps
    hg clone http://hg.mozilla.org/services/server-core/
    cd server-core
3. Install bipostaldash

   bin/python setup.py install 

4. Start the server::

    paster serve etc/bipostaldash-dev.ini


Run the Server
--------------
::

    paster serve etc/bipostaldash-dev.ini


The API
-------

::

    GET /alias/
    >>> 200 OK {"email": <email>, "aliases": [<alias>, <alias>, ...]}

    Retrieve all the aliases for the current user.

    Requires browserid auth.

::

    POST /alias/
    >>> 200 OK {"email": <email>, "alias": <alias>}

    Create a new alias for the current user.

    Optionally, an alias can be requested in the POST body:

        {"alias": <alias>}

    Requires browserid auth.

::

    GET /alias/<alias>
    >>> 200 OK {"email": <email>}

    Get the real email address for the given alias.

    No auth required.

::

    DELETE /alias/<alias>
    >>> 200 OK

    Forget about the given alias.

    Requires browserid auth.

::

    PUT /alias/<alias>
    >>> 200 OK

    Modify the given alias by passing these properties in the body::

        {"active": true|false}

    Requires browserid auth.
