<!DOCTYPE html>
<html>
    <head>
        <title>Please log in</title>
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
      <h1>Please Log In</h1>
      <div id="browserid"><img src="https://browserid.org/i/sign_in_grey.png" id="signin"></div>
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.4/jquery.min.js" type="text/javascript"></script>
      <script src="http://browserid.org/include.js" type="text/javascript"></script>
      <script type="text/javascript">
          $(function() {
          $('#signin').click(function(){
              navigator.id.getVerifiedEmail(function(assertion) {
                  var form = $("<form method='POST' action='/' >" +
                      "<input type='hidden' name='assertion' value='" + assertion +
                      "'/><input type='hidden' name='audience' value='bipostal.browserid.org'>" + 
                      "</form>").appendTo('#browserid');
                  form.submit();
              })
          });
          $('#signin').attr('src', "https://browserid.org/i/sign_in_blue.png");
      });
      </script>
  </body>
</html>
