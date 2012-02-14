/* MACAuth
 *  Depends on 
 *      crypto-js (http://code.google.com/p/crypto-js/)
 *
 * <script type="text/javascript" src="http://crypto-js.googlecode.com/files/2.5.3-crypto-sha1.js"></script>
 * <script type="text/javascript" src="http://crypto-js.googlecode.com/files/2.5.3-crypto-sha256.js"></script>
 *
 */
var MACAuth;

if (MACAuth === undefined)
{
    MACAuth = function (args)
    {
        var self = {};
        self._init=args;
        self._args=self._init;

        // General configuration options.
        
        self._default_signature_method= "mac-sha-1";
        self._nonce_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";


        self.reset = function() {
            this._args=self._init;
            this.sbs=undefined;
            return this;
        };

        self.b64encoder = function(string) {
            if (window.btoa) {
                return window.btoa(string);
            }
            throw ('Crap, no btoa!');
        };

        /** Set the target URL (does not include the parameters)
         *
         * @param path {string} the fully qualified URI (excluding query arguments) (e.g "http://example.org/foo")
         */
        self.setFromURL = function (path) {
            re = new RegExp('((https?)://([^:/]+)(:(\\d+))?)?(/.*)?');
            if (path == '') {
                throw ('No path specified for MACAuth.setURL');
            }
            matches = re.exec(path);
            self._args['host'] = matches[3];
            if (!self._args['host']) {
                self._args['host'] = document.location.host;
            }
            if (matches[5]){
                self._args['port'] = matches[5];
            } else {
                if (matches[2] && matches[2].indexOf('s') > 0){
                    self._args['port'] = '443';
                } else {
                    self._args['port'] = document.location.port || '80';
                }
            }
            self._args['uri'] = matches[6];
            return this;
        };

        /** set the "action" for the url, (e.g. GET,POST, DELETE, etc.)
         *
         * @param action {string} HTTP Action word.
         */
        self.setAction = function(action) {
            if (action === undefined) {
                action="GET";
                }
            action = action.toUpperCase();
            if (action.match('[^A-Z]')) {
                throw ('Invalid action specified for MACAuth.setAction');
                }
            this._action = action;
            return this;
        };

        self._checkKeys = function(keys) {
            if (keys) {
                self._args = self._merge(keys, self._args);
            }
            if (!self._args['access_token']) {
                throw ('Missing public "access_token"');
            }
            if (!self._args['mac_key']) {
                throw ('Missing secret "mac_key"');
            }
            return self._args;
        }

        /** set the signature method (currently only Plaintext or SHA-MAC1)
         *
         * @param method {string} Method of signing the transaction (only PLAINTEXT and SHA-MAC1 allowed for now)
         */
        self.setSignatureMethod = function(method) {
            if (method === undefined) {
                method = this._default_signature_method;
                }
            if (method.toUpperCase().match(/(mac-sha-1|mac-sha-256)/) === undefined) {
                throw ('Unknown signing method specified for MACAuth.setSignatureMethod');
                }
            this._args['mac_algorithm'] = method;
            return this;
        };

        /** sign the request
         *
         * note: all arguments are optional, provided you've set them using the
         * other helper functions.
         *
         * @param args {object} hash of arguments for the call
         *                   {action:, path:, parameters:, method:, signatures:}
         *                   all arguments are optional.
         */
        self.sign = function (args) {
            args = self._merge(args, self._args);
            // Set any given parameters
            if(args['action'] == undefined) {
                args['action'] = 'GET';
                }
            if (args['port'] == undefined) {
                port = '80';
            }
            if (args['uri'] == undefined) {
                args['uri'] = '/';
                }
            if (args['mac_algorithm'] == undefined) {
                args['mac_algorithm'] = 'mac-sha-1';
                }
            if (args['host'] == undefined) {
                args['host'] == 'localhost';
            }
            if (args['ext'] == undefined) {
                args['ext'] = '';
            }
            self._checkKeys(args);
            if (!args['nonce']) {
                args['nonce'] = self._getNonce();
            }
            if (!args['ts']) {
                args['ts'] = self._getTimestamp();
            }

            var sb = [args['ts'], 
                args['nonce'], 
                args['action'].toUpperCase(),
                args['uri'],
                args['host'],
                args['port'],
                args['ext']];
            var sbs = sb.join("\n") + "\n";
            var sha = Crypto.SHA1;
            if (args['mac_algorithm'].toLowerCase() == 'mac-sha-256') {
                sha = Crypto.SHA256;
            }
            // console.debug(sbs);
            mac = self.b64encoder(Crypto.HMAC(sha, sbs, args['mac_key'], {asString: true}));
            return {
                signature: mac,
                sbs: sbs,
                header: 'MAC id="' + args['access_token'] +
                    '", ts="' + args['ts'] +
                    '", nonce="' + args['nonce'] +
                    '", ext="' + args['ext'] + 
                    '", mac="' + mac + '"'
                };
        };

        // Start Private Methods.

        self._getNonce = function (length) {
            if (length === undefined) {
                length=5;
                }
            var result = "",
                i=0,
                rnum,
                cLength = this._nonce_chars.length;
            for (;i<length;i++) {
                rnum = Math.floor(Math.random()*cLength);
                result += this._nonce_chars.substring(rnum,rnum+1);
            }
            return this._nonce = result;
        };

        self._sizeoOf = function(obj) {
            if (obj == undefined) {
                return 0;
            }
            var size = 0, key;
            for (key in obj) {
                if (obj.hasOwnProperty(key)){
                    size++;
                }
            }
            return size;
        };

        self._getTimestamp = function() {
            var ts = Math.floor((new Date()).getTime()/1000);
            return this._timestamp = ts;
        };

        self._merge = function(source,target) {
            if (source == undefined)
                source = {};
            if (target == undefined)
                target = {};
            for (var key in source) {
                target[key] = source[key];
            }
            return target;
        }

    return self;
    };
}
