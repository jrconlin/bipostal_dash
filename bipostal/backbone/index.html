<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Manage your BrowserID aliases</title>
    <script src="jquery-underscore-backbone.js"></script>
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
      <h2>Primary Address: <span id="email"></span></h2>
    </hgroup>
    <button id="new">Get a new alias.</button>
    <ul id="aliases">
    </ul>
    <script>
      "use strict";
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

        destroy: function() {
          $(this.el).remove();
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
          $.post(this.aliases.url, function(response) {
            self.aliases.add(response);
          });
        }
      });
      window.App = new AppView;
    </script>
  </body>
</html>
