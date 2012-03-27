
console.debug('starting binject');

var bp = new function() {

    var host = 'http://10.250.2.176';

    this.data = {
        'siteName': document.getElementById('sitename').innerHTML,
        'referrer': document.referrer,
        'worker': undefined,
        'host': host,
        'cb': {}
    };

    this.rnd = function(maxRand) {
        return Math.floor(Math.random() * maxRand);
    };

    this.sendCmd = function(uri, args) {
        console.debug('sending command ' + uri);
        id = this.rnd(1000000);
        if (args == undefined) {
            args = {};
        }
        args['callback_id'] = 'c_' + id;
        try {
            this.data.cb[args.callback_id] = {'success': args.success,
                'error': args.error};
            var send = JSON.stringify({'cmd': uri, 'args': args });
            console.debug('posting ' + send)
            this.data.worker.contentWindow.postMessage(send,
                this.data.host);
        } catch (e)  { // ...if e instanceof FooError
            console.error('Exception: ', e);
            if (this.data.cb[args.callback_id].error) {
                this.data.cb[args.callback_id].error({'exception': e});
            }
            delete this.data.cb[args.callback_id];
        }
    };

    this.recvMsg = function(event){
        log.debug(event.origin);
        try {
            rep = JSON.parse(event.data);
            if (rep.callback_id) {
                callback = this.data.cb[rep.callback_id];
                delete this.data.cb[rep.callback_id];
                delete rep.callback_id;
                if (callback && callback.success) {
                    return callback.success(rep);
                }
            }
            log.debug('No callback present');
        } catch (e) {
            console.error('Exception: ', e);
        }
    };

    this.getAliases = function(host) {
        console.info('checking aliases');
        if (host == undefined) {
            host = this.data.host;
        }
        this.sendCmd('aliases',
                {'origin': host,
                 'success': function(resp) { 
                console.info('got aliases');
                rep = JSON.parse(resp);
                if (rep.data && rep.data.length) {
                    // TODO add items from response as addresses
                } else {
                    // TODO display the "Generate" link
                    var bpElement = document.createElement('a');
                    bpElement.href = '#';
                    bpElement.className = 'emphasize';
                    bpElement.innerHTML = "Generate an alias for this site";
                    bpElement.addEventListener('click', bp.getAlias, false);
                    var une = document.getElementById('useNewEmail').parentNode;
                    une.appendChild(document.createElement('br'));
                    une.appendChild(bpElement);
                }
            }})
    };

    this.init = function() {
        if (document.getElementById('scripts') == undefined) {
            var scr = document.createElement('div');
            document.getElementsByTagName('body')[0].appendChild(scr);
        }
        var worker = document.createElement('iframe');
        alert (this.data.host + '/worker.html');
        worker.id = 'worker';
        worker.src = this.data.host + '/worker.html';
        //worker.style.display='none';
        document.getElementsByTagName('body')[0].appendChild(worker);
        worker.contentWindow.addEventListener('message', this.recvMsg, false);
        this.data.worker = worker;
        
    };

    this.init();

    return {
        'data': this.data,
        'getAliases': this.getAliases,
        'sendCmd': this.sendCmd,
        'recvMsg': this.recvMsg,
        'rnd': this.rnd,
        'obj': this
    }
}();

var une = document.getElementById('useNewEmail').parentNode;
var bpM = document.createElement('a');
bpM.href = 'http://bipostal.diresworb.org/';
bpM.className = 'emphasize';
bpM.innerHTML = "Manage your aliases";
une.appendChild(document.createElement('br'));
une.appendChild(bpM);
console.info('here');
bp.getAliases(document.getElementById('sitename').innerHTML)
