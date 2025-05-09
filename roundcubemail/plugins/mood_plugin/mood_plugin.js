$(document).ready(function() {
  if (!window.rcmail) return;
  
  rcmail.addEventListener('init', function() {
    console.log("Mood plugin: Roundcube init");

    window.addEventListener('message', function(event) {
      console.log("Mood plugin: got postMessage", event);

      
      if (event.origin !== 'https://localhost:5000') {
        console.warn(" Ignoring message from", event.origin);
        return;
      }

      if (event.data && event.data.type === 'mood-selected') {
        var data = event.data.data;
        console.log(" Mood plugin: mood-selected payload", data);
        rcmail.display_message(
          'The mood detected was: ' + data.dominant_emotion,
          'info'
        );
      }
    }, false);

    
    rcmail.init_mood_plugin = function() {
      rcmail.register_command('detect-mood',
        function() {
          console.log(" Mood plugin: opening camera window");
          window.open(
            'https://localhost:5000/camera',
            'mood_detector',
            'width=700,height=650,resizable=yes'
          );
        },
        true
      );
    };
    rcmail.init_mood_plugin();
  });
});
