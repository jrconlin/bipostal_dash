<!DOCTYPE html>
<%
    user = pageargs.get('user', 'User')
    request = pageargs.get('request', {'registry': {}})
    consumer_key = request.registry.get('config', {}).get('auth.oauth.consumer_key', '')
    shared_secret = request.registry.get('config', {}).get('auth.oauth.shared_secret', '')

%>
<html>
  <head>
    <meta charset="utf-8">
    <title>Manage your BrowserID aliases</title>
    <style>
      body {
        color: #333;
      }
      h2 {
        font-size: 1.17em;
      }
      #email {
        color: #D95B43;
      }
      #aliases {
        display: table;
        padding: 0;
      }
      #aliases li {
        line-height: 2em;
        display: table-row;
        font-family: monospace;
        -moz-transition-property: *;
        -moz-transition-duration: .75s;
      }
      #aliases li.new {
        background-color: #ECD078;
      }
      #aliases li span, #aliases li a {
        display: table-cell;
      }
      #aliases li span {
        padding-right: 2em;
      }
    </style>
  </head>
  <body>
    <hgroup>
      <h1>Manage your BrowserID Aliases</h1>
      <h2>Primary Address: <span id="email">${user}</span></h2>
      </hgroup>
      <label for="audience">Audience:</label>
      <input name="audience" id="audience" value="example.com">
      <button id="new">Get a new alias.</button>
    <ul id="aliases">
    </ul>
    <script src="jquery-underscore-backbone.js"></script>
    <script src="/OAuthSimple.js" type="text/javascript"></script>
    <script>
        "use strict";

        Backbone.old_sync = Backbone.sync;

        jQuery.ajaxPrefilter( function (options, originalOptions, jqXHR){
            console.debug(options, originalOptions, jqXHR);
            var oauth = OAuthSimple('${consumer_key}', '${shared_secret}');
            var elem = options.url.split('?')
            var path = elem[0];
            var params = elem[1]?elem[1]:'';
            /*            
            if (options.data) {
                if (params.length) { 
                    params += '&';
                }
                params += options.data;
            }
            */            
            // Unescaping path because jquery already escaped it.
            var signed = oauth.sign({action: options.type,
                path: unescape(path),
                parameters: unescape(params)});
            options.url = signed.signed_url;
            }
        );
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
          'click .delete': 'destroy'
        },

        destroy: function(o) {
            $(this.el).remove();
            console.debug(o);
            console.debug(this);
          this.model.destroy();
          return false;
        },

        render: function() {
          var html = '<span>' + this.model.get('alias') + '</span>';
          html += '<a class="delete" href="#" title="Delete this alias">[x]</a>';
          $(this.el).html(html);
          return this;
        }
      });

      var AppView = Backbone.View.extend({
        el: $('body'),

        initialize: function() {
          this.aliases = new Aliases;
          this.aliases.bind('reset', this.render, this);
          this.aliases.bind('add', this.append, this);
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
          'click #new': 'newAlias'
        },

        newAlias: function() {
            var self = this;
            var audience = $('#audience')[0].value;
            $.post(this.aliases.url, 
            '{"audience": "' + audience + '"}',
            function(response) {
                self.aliases.add(response);
            });
        }
      });
      window.App = new AppView;
    </script>
  </body>
</html>
