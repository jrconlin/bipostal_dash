document.getElementById('sitename').innerHTML = 'localhost';

var bp = new function() {

    var host = 'http://192.168.56.101';

    this.data = {
        'siteName': document.getElementById('sitename').innerHTML,
        'referrer': document.referrer,
        'worker': undefined,
        'cb': {}
    };

    this.rnd = function(maxRand) {
        return Math.floor(Math.random() * maxRand);
    }

    this.sendCmd = function(uri, args) {
        id = this.rnd(1000000);
        if (args == undefined) {
            args = {};
        }
        args['callback_id'] = 'c_' + id;
        try {
            this.data.cb[args.callback_id] = {'success': args.success,
                'error': args.error};
            this.data.worker.postMessage(JSON.stringify(
                    {'cmd': uri,
                     'args': args}),
                this.host);
        } catch (e)  { // ...if e instanceof FooError
            console.error('Exception: ', e);
            if (this.data.cb[args.callback_id].error) {
                this.data.cb[args.callback_id].error({'exception': e});
            }
            delete this.data.cb[args.callback_id];
        }
    }

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
    }

    this.getAliases = function(host) {
        this.sendCmd('/origin/'+host,
            function(resp) { 
                // TODO add items from response as addresses
            }

    }

    this.init = function() {
        if (document.getElementById('scripts') == undefined) {
            var scr = document.createElement('div');
            document.getElementsByTagName('body')[0].appendChild(scr);
        }
        var worker = document.createElement('iframe');
        alert (host + '/worker.html');
        worker.id = 'worker';
        worker.src = host + '/worker.html';
        //worker.style.display='none';
        worker.addEventListener('message', this.recvMsg, false);
        document.getElementsByTagName('body')[0].appendChild(worker);
        this.data.worker = worker;
        
    }

    this.init();

    return {
        'data': this.data,
        'sendCmd': this.sendCmd
    }
}();

var bpElement = document.createElement('a');
bpElement.href = '#';
bpElement.className = 'emphasize';
bpElement.innerHTML = "Generate an alias for this site"

var une = document.getElementById('useNewEmail').parentNode;
//TODO Add link to "manage your aliases" (punts to create new window)


une.appendChild(document.createElement('br'));
une.appendChild(bpElement);
