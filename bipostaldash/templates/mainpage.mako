<!DOCTYPE html>
<%
    import time

    user = pageargs.get('user', 'User')
    request = pageargs.get('request', {'registry': {}})
    keys = pageargs.get('keys', {
        'access_token': request.registry.get('config', 
            {}).get('auth.mac.access_token', ''),
        'secret': request.registry.get('config', 
        {}).get('auth.mac.mac_key', ''),
        'server_time': int(time.time())})

%>
<html>
  <head>
    <meta charset="utf-8">
    <title>Manage your BrowserID aliases</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
  </head>
  <body>
    <hgroup>
      <h1>Manage your BrowserID Aliases</h1>
      <h2>Primary Address: <span id="email">${user}</span></h2>
      </hgroup>
      <span id="aud">
          <label for="audience">Audience:</label>
          <input name="audience" id="audience" value="bipostal.diresworb.org">
      </span>
      <button id="new">Get a new alias.</button>
    <ul id="aliases">
    </ul>
    <footer>
    <button id="logout">Logout</button>
    </footer>
    <!-- dev version 
    <script src="jquery-1.7.1.js"></script>
    <script src="underscore.js"></script>
    <script src="backbone.js"></script>
    -->
    <!-- minified version --> 
    <script src="jquery-underscore-backbone.js"></script>
    <script type="text/javascript" src="http://crypto-js.googlecode.com/files/2.5.3-crypto-sha1-hmac.js"></script>
    <script type="text/javascript" src="http://crypto-js.googlecode.com/files/2.5.3-crypto-sha256-hmac.js"></script>
    <script src="/MACAuth.js" type="text/javascript"></script>
    <script type="text/javascript">

        Backbone.old_sync = Backbone.sync;

        var methodMap = {
            'create': 'POST',
            'update': 'PUT',
            'delete': 'DELETE',
            'read': 'GET',
        };

        var disable_labels = {
            true: 'enable',
            false: 'disable'
        }
    
        // Sadly, copied wholesale from the source with one minor change.
        Backbone.sync = function (method, model, options) {
            var type = methodMap[method];
            var params = {type: type, dataType: 'json'};

            var getValue = function(object, prop) {
                if (!(object && object[prop])) return null;
                return _.isFunction(object[prop]) ? object[prop]() : object[prop];
            };
            
            if (!options.url) { 
                params.url = getValue(model, 'url') || urlError();
            }
            if (!options.data && model && (method == 'create' || method == 'update')) {
                params.contentType = 'application/json';
                params.data = JSON.stringify(model.toJSON());
            }

            if (Backbone.emulateJSON) {
                params.contentType = 'application/x-www-form-urlencoded';
                params.data = params.data ? {model: params.data} : {};
            }

            if (Backbone.emulateHTTP) {
                if (type === 'PUT' || type === 'DELETE') {
                    if (Backbone.emulateJSON) params.data._method = type;
                        params.type = 'POST';
                        params.beforeSend = function(xhr) {
                        xhr.setRequestHeader('X-HTTP-Method-Override', type);
                    };
                }
            }

            if (params.type !== 'GET' && !Backbone.emulateJSON) {
                params.processData = false;
            }

            // add the signature
            var skew =Math.floor(new Date().getTime() / 1000) - ${keys.get('server_time', int(time.time()))};
            //console.debug('Skew = ' + skew);
            var macauth = new MACAuth({'access_token': '${keys.get('access_token')}', 
                    'mac_key': '${keys.get('mac_key')}',
                    'skew': skew,
                    'port': '80'}).setAction(params.type).setFromURL(params.url).sign();
            if (!params.headers) {
                params.headers = {'Authorization': macauth.header}
            }else{
                params.headers['Authorization'] = macauth.header;
            }
            return $.ajax(_.extend(params, options));
      };

      var Alias = Backbone.Model.extend({
          initialize: function(attributes) {
          this.id = attributes.alias;
        },
        });

      var Aliases = Backbone.Collection.extend({
          model: Alias,

          url: '/alias/',
          parse: function(response) {
             this.email = response.email;
             return response.aliases;
          }
      });

      var AliasView = Backbone.View.extend({
        tagName: 'li',

        events: {
        'click .delete': 'destroy',
        'click .disable': 'toggle'
        },

        toggle: function(o) {
            ret = this.model.save('status',  
                    (this.el.classList.contains('inactive') ? 'active' : 'inactive'),
                    {
                        success: function (model, response) {
                        // jquery has problems with $('#' + response.alias)
                            li = document.getElementById(response.alias);
                            $(li).toggleClass('inactive');
                            lih = li.getElementsByClassName('disable')[0];
                            lih.innerHTML = disable_labels[lih.innerHTML == disable_labels[false]]
                        }
                    }
                )
            //console.debug(ret);
           //     this.el.classList.toggle('inactive');
            return false;
        },

        destroy: function(o) {
            $(this.el).remove();
            //console.debug(o);
            //console.debug(this);
          this.model.destroy();
          return false;
        },

        render: function() {
            //console.debug(this.model);
            var alias = this.model.get('alias');
            var cls = this.model.get('status') || 'active';
            var html = '<span>' + alias + '</span>';
            html += '<span="controls"><button class="disable" title="Toggle availability">';
            html += disable_labels[cls != 'active'];
            html += '</button>';
            html += '<button class="delete" title="Delete this alias">X</button>';
            //console.debug(this.el, $(this.el));
            this.el.id = alias;
            if (cls != 'active') {
                  this.el.classList.add(cls);
            }
            $(this.el).html(html);
            return this;
        }
      });

      var AppView = Backbone.View.extend({
        el: $('body'),

        initialize: function() {
          //console.debug('initialize');
          this.aliases = new Aliases;
          //console.debug('binding');
          this.aliases.bind('reset', this.render, this);
          this.aliases.bind('add', this.append, this);
          this.aliases.bind('logout', this.logout, this);
          //console.debug('bound logout');
          this.aliases.fetch();
        },

        render: function() {
          this.$('#email').text(this.aliases.email);
          this.aliases.each(this.append, this);
          $(this).addClass('loaded');
          this.loaded = true;
        },

        append: function(alias) {
          var view = new AliasView({model: alias});
          var el = $(view.render().el).appendTo('#aliases');
          if (this.loaded) {
            el.addClass('new');
            setTimeout(function(){ el.removeClass('new'); }, 200);
          }
        },

        events: {
            'click #new': 'newAlias',
            'click #logout': 'logout'
        },

        newAlias: function() {
            var self = this;
            //console.debug('new_alias');          
            var audience = $('#audience')[0].value;
            var skew = Math.floor(new Date().getTime() / 1000) - ${keys.get('server_time', int(time.time()))};
            var macauth = new MACAuth({'access_token': '${keys.get('access_token')}', 
                    'skew': skew,
                    'mac_key': '${keys.get('mac_key')}'}).setAction('POST').setFromURL(this.aliases.url).sign();
            $.ajax({url:this.aliases.url, 
                    type: 'POST',
                    datatype: 'json',
                    data: '{"audience": "' + audience + '"}',
                    success: function(response) {
                        self.aliases.add(response);
                        },
                    headers:{'Authorization': macauth.header},
                    });
        },

        logout: function () {
            var self = this;
            var skew = Math.floor(new Date().getTime() / 1000) - ${keys.get('server_time', int(time.time()))};
            var macauth = new MACAuth({'access_token': '${keys.get('access_token')}', 
                    'skew': skew,
                    'mac_key': '${keys.get('mac_key')}'}).setAction('DELETE').setFromURL('/').sign();
            $.ajax({url: '/',
                    type: 'DELETE',
                    headers:{'Authorization': macauth.header},
                    contentType: 'application/javascript',
                    success: function (data, status, xhr) {
                        document.location = "/";
                    },
                    error: function (xhr, status, error){
                        console.error(status);
                        console.error(error);
                        $('#logout').disable();
                    }
                })
        }
      });

      window.App = new AppView;

    </script>
  </body>
</html>
