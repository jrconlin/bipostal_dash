// ==UserScript==
// @name           addBipostal
// @namespace      browserid.org
// @description    Add Bipostal Login to Browserid
// @include        https://browserid.org/sign_in
// ==/UserScript==

var bp = new function() {
    
    var host = 'http://10.250.2.176';

    var data = {
        'siteName': document.getElementById('sitename').innerHTML,
        'referrer': document.referrer,
        'cb': {},
    };

    
    this.sendCmd(uri, callback) {
        var id = 'bp_' + Math.floor(Math.random() * 1000000)l
        var path = host + uri;
        (function(id, path, callback) {
            this.data.cb[id] = function(event) {
                callback(event, target);
                k = document.getElementById(id);
                k.parentNode.removeChild(k);
                delete(cb[id]);
            }
            scr = document.createElement('script');
            scr.id = id;
            prefix = '?';
            if (path.indexof('?' != -1) {
                prefix = '&';
            }
            scr.src = path + prefix + 'callback=bp.data.cb.' + id;
            document.getElementById('scripts').appendChild(scr);
        }) (id, path, callback)
    }

    this.isLoggedIn = function() {
        
    }


    this.init = function() {
        if (document.getElementById('scripts') == undefined) {
            var scr = document.createElement('div');
            document.getElementById('body')[0].appendChild(scr);
        }
        var worker = document.createElement('iframe');
        worker.href = host + '/worker.js

    }

    this.init();

    return {
        'data': this.data,
    }
} ();

var bpElement = document.createElement('a');
bpElement.href = '#';
bpElement.innerHtml = "Generate an alias for this site"

var une = document.getElementById('useNewEmail');

