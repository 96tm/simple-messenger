window.setInterval(function() {
    let alerts = document.querySelectorAll("div.alert");
    let container = document.querySelector(".flashed-messages");
    for (alertMessage of alerts) {
      console.log(alertMessage)
      var fadeEffect = setInterval(function () {
          if (alertMessage && !alertMessage.style.opacity) {
            alertMessage.style.opacity = 1;
          }
          if (alertMessage && alertMessage.style.opacity > 0) {
            alertMessage.style.opacity -= 0.1;
          } 
          else {
              clearInterval(fadeEffect);
              if (container.contains(alertMessage)) {
                container.removeChild(alertMessage);
              }
          }
      }, 120);
    }
  }, 1500);