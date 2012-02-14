<!DOCTYPE html>
<html>
    <head>
        <title>Please log in</title>
        <link rel="stylesheet" type="text/css" href="style.css" />
  </head>
  <body>
      <hgroup>
      <h1>Manage your BrowserID Aliases</h1>
      <h2>Please Log in</h2>
      </hgroup>
      <div id="browserid"><img src="https://browserid.org/i/sign_in_grey.png" id="signin"></div>
      <footer>&nbsp;</footer>
      <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.4/jquery.min.js" type="text/javascript"></script>
      <script src="http://browserid.org/include.js" type="text/javascript"></script>
      <script type="text/javascript">
          $(function() {
             $('#signin').click(function(){
              document.getElementsByTagName('body')[0].style.cursor='wait';
              navigator.id.getVerifiedEmail(function(assertion) {
                  document.getElementsByTagName('body')[0].style.cursor='auto';
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
