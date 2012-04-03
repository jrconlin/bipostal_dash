<!DOCTYPE html>
<%
    import time

    session = pageargs.get('session', {})
    config = pageargs.get('config', {})
    request = pageargs.get('request', {'registry': {}})
    keys = session.get('keys', {
        'access_token': request.registry.get('config', 
            {}).get('auth.mac.access_token', ''),
        'secret': request.registry.get('config', 
        {}).get('auth.mac.mac_key', ''),
        'server_time': int(time.time())})

%>
<html>
  <head>
    <meta charset="utf-8">
  </head>
  <body>
    <!-- dev version 
    <script src="jquery-1.7.1.js"></script>
    <script src="underscore.js"></script>
    <script src="backbone.js"></script>
    -->
    <!-- minified version --> 
    <div id="m"></div>
    <script type="text/javascript" src="http://crypto-js.googlecode.com/files/2.5.3-crypto-sha1-hmac.js"></script>
    <script type="text/javascript" src="http://crypto-js.googlecode.com/files/2.5.3-crypto-sha256-hmac.js"></script>
    <script src="/MACAuth.js" type="text/javascript"></script>
    <script type="text/javascript">
    var xhr;
    var callbacks = {};


    if (window.XMLHttpRequest) {
        xhr = new XMLHttpRequest();
    } else if (window.ActiveXObject) {
        xhr = new ActiveXObject("Microsoft.XMLHTTP");
    }

    function log (msg) {
        //document.getElementById('m').innerHTML += msg + "<br>";
        console.debug(msg);
    }

    function handleReply(resp) {
        log (xhr.readyState);
        if (xhr.readyState === 4) {
            log ('handling reply');
            var reply;
            log(resp.target);
            reply = {"status": false};
            if (resp != undefined && resp.target.status == 200) {
                if (resp.target.responseText) {
                    reply = JSON.parse(resp.target.responseText);
                }
            }
            callbackRec = callbacks[reply.callback];
            if (callbackRec) {
                callbackRec.event.source.postMessage(resp.target.responseText,
                    callbackRec.event.origin);
                delete (callbacks[reply.callback]);
            }
            resp.stopImmediatePropagation();
        }
        
    }

    window.addEventListener('message', function(event) {
            log(" origin: " + event.origin);
            log(" data:   " + event.data);

            var cmd = JSON.parse(event.data);
            var url = '';
            var method = '';
            var callback = cmd.args.callback || Math.floor(Math.random() * 1000000);
            var args = undefined;
            callbacks[callback] = {'event': event};

            switch (cmd.cmd) {
                case 'aliases':
                    url = '/origin/' + cmd.args.origin +
                        '?callback=' + callback;
                    method = 'GET';
                    break;
                case 'newalias':
                    url = '/alias/';
                    method = 'POST';
                    args = {'audience': cmd.args.origin,
                        'callback': callback};
                    break;
                case 'logggedin':
                    url = '/user/' + 
                        '?callback=' + callback;
                    method = 'GET';
                    break;
                default:
                    event.source.postMessage(JSON.stringify({'status': false,
                            'callback': cmd.callback}),
                        event.origin);
                    return false;
            }
            xhr.open(method, url);
            xhr.setRequestHeader('Content-Type', 'application/json');
            // add the signature
            var skew =Math.floor(new Date().getTime() / 1000) - ${keys.get('server_time', int(time.time()))};
            //console.debug('Skew = ' + skew);
            var macauth = new MACAuth({'access_token': '${keys.get('access_token')}', 
                    'mac_key': '${keys.get('mac_key')}',
                    'skew': skew,
                    'port': '80'}).setAction(method).setFromURL(url).sign();
            xhr.setRequestHeader('Authorization', macauth.header);
            xhr.onreadystatechange = handleReply;
            log('sending event');
            if (args) {
                args = JSON.stringify(args);
            }
            xhr.send(args);
      }, false);
    </script>
  </body>
</html>
