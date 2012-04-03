console.debug('starting binject');

var bp = new function() {

    var host = 'http://10.250.2.176';

    this.data = {
        'sitename': document.getElementById('sitename').innerHTML,
        'referrer': document.referrer,
        'worker': undefined,
        'host': host,
        'cb': {}
    };

    this.rnd = function(maxRand) {
        return Math.floor(Math.random() * maxRand);
    };

    this.sendCmd = function(uri, args) {
        //console.debug('sending command ' + uri);
        id = this.rnd(1000000);
        if (args == undefined) {
            args = {};
        }
        args['callback'] = 'c_' + id;
        try {
            this.data.cb[args.callback] = {'success': args.success,
                'error': args.error};
            var send = JSON.stringify({'cmd': uri, 'args': args });
            //console.debug('posting ' + send + ' ' + this.data.host)
            this.data.worker.contentWindow.postMessage(send,
                this.data.host);
        } catch (e)  { // ...if e instanceof FooError
            //console.error('Exception: ', e);
            if (this.data.cb[args.callback].error) {
                this.data.cb[args.callback].error({'exception': e});
            }
            delete this.data.cb[args.callback];
        }
    };

    this.recvMsg = function(event){
        //console.debug(event.origin);
        try {
            rep = JSON.parse(event.data);
            if (rep.callback) {
                callback = bp.data.cb[rep.callback];
                delete bp.data.cb[rep.callback];
                delete rep.callback;
                if (callback && callback.success) {
                    return callback.success(rep);
                }
            }
            //console.debug('No callback present');
        } catch (e) {
            console.error('Exception: ', e);
        }
        if (callback && callback.error) {
            return callback.error(rep);
        }
        return false;
    };

    this.newAlias = function() {
        bp.sendCmd('newalias',
                {'origin': bp.data.sitename,
                'success': function(resp) {
                    bp.addAlias({'results': [resp]});
                    genLink = document.getElementById('newAlias');
                    genLink.parentNode.removeChild(genLink);
                    }
                })
    };

    this.addAlias = function(resp){
        //console.info('got aliases');
        if (resp.results && resp.results.length) {
            //console.info('got data');
            //console.info(resp.results);
            mailList = document.getElementById('selectEmail').getElementsByClassName('inputs')[0];
            for (i=0; i < resp.results.length; i++) {
                alias = resp.results[i];
                addr = document.createElement('li');
                aliasName = 'alias' + i;
                addr.innerHTML = '<label class="serif selectable" title="Alias for '+
                    alias.origin + '" for="' + aliasName +'" ><input id="' + aliasName +
                    '" type="radio" value="' + alias.alias + '" name="email" />' +
                    "Alias for " + alias.origin + "</label>";
                    mailList.appendChild(addr);
            }
        }
    };

    this.getAliases = function(host) {
        //console.info('checking aliases');
        if (host == undefined) {
            host = this.data.host;
        }
        this.sendCmd('aliases',
                {'origin': host,
                 'success': function(resp) {
                 if (resp.results && resp.results.length) {
                    bp.addAlias(resp);
                 } else {
                    var bpElement = document.createElement('a');
                    bpElement.href = '#';
                    bpElement.className = 'emphasize';
                    bpElement.id = 'newAlias';
                    bpElement.innerHTML = "Generate an alias for this site";
                    bpElement.addEventListener('click', bp.newAlias, false);
                    var une = document.getElementById('useNewEmail');
                    une.parentNode.insertBefore(document.createElement('br'), une);
                    une.parentNode.insertBefore(bpElement,une);
                }
            }
            })
    };

    this.init = function() {
        if (document.getElementById('scripts') == undefined) {
            var scr = document.createElement('div');
            document.getElementsByTagName('body')[0].appendChild(scr);
        }
        var worker = document.createElement('iframe');
        worker.id = 'worker';
        worker.src = this.data.host + '/s/worker';
        worker.style.display = 'none';
        worker.addEventListener('load',
                function(){
                    bp.getAliases(bp.data.sitename);
                }, false);
        document.getElementsByTagName('body')[0].appendChild(worker);
        window.addEventListener('message', this.recvMsg, false);
        this.data.worker = worker;
        window.my_worker = worker;
        //console.info('built worker');
    };

    this.init();

    return {
        'data': this.data,
        'getAliases': this.getAliases,
        'addAlias': this.addAlias,
        'newAlias': this.newAlias,
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
