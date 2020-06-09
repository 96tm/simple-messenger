function scrollMessageAreaToBottom() {
  let messageArea = document.getElementById("message-area-id");
    if (messageArea) {
      messageArea.scrollTo(0, messageArea.scrollHeight);
    }
}

function add_message(messageArea, currentUsername, contactUsername, message) {
  let text = message["text"];
  let timestamp = message["timestamp"];
  let username;
  if (message["sender_username"] === currentUsername) {
      username = "You";
  }
  else {
      username = contactUsername;
  }
  let messageDiv = document.createElement("div");
  let messageSpan = document.createElement("span");
  let timestampSpan = document.createElement("span");
  let textSpan = document.createElement("span");
  let b = document.createElement("b");
  let br = document.createElement("br");
  b.innerText = username + " ";
  textSpan.innerText = text;
  timestampSpan.innerText = timestamp + "\n";
  messageSpan.appendChild(b);
  messageSpan.appendChild(timestampSpan);
  messageSpan.appendChild(br);

  messageDiv.appendChild(messageSpan);
  messageDiv.appendChild(br);
  messageDiv.appendChild(textSpan);
  messageDiv.setAttribute("class", "message");

  messageArea.appendChild(messageDiv);
  messageArea.appendChild(br);
  scrollMessageAreaToBottom();
}   

function send_message(recipient_id, message_text){
    let text = message_text.trim();
    if (text) {
        let request = new XMLHttpRequest();
        request.open("POST", "/send_message", true);
        request.setRequestHeader("Content-Type", "application/json");
        request.setRequestHeader("Content-Encoding", "UTF-8");
        request.onload = function(){
            try {
                if (request.readyState === request.DONE) {
                  if (request.status === 200) {
                    let response = JSON.parse(request.response);
                    let message = response["message"];
                    let contactUsername = response["contact_username"];
                    let currentUsername = response["current_username"];
                    let messageArea = document.getElementById("message-area-id");
                    document.getElementById("message-field-id").value = "";
                    add_message(messageArea, currentUsername, contactUsername, message);
                  } else {
                    alert('There was a problem with the request.');
                  }
                }
              }
              catch(e) {
                alert('Caught Exception: ' + e.description);
                console.log('Caught Exception: ' + e.description);
              }
        }
        let data = {
                        message: text,
                        recipient_id: recipient_id
                   };
        request.send(JSON.stringify(data));
    }
}

function add_messages(currentUsername, contactUsername, messages) {
    let messageArea = document.getElementById("message-area-id");
    messageArea.innerHTML = "";
    for (let index = 0; index < messages.length; index++) {
        message = messages[index];
        add_message(messageArea, currentUsername, contactUsername, message);
    }
}   

function choose_contact(contactId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/choose_contact", true);
    request.setRequestHeader("Content-Type", "application/json");
    request.setRequestHeader("Content-Encoding", "UTF-8");
    request.onload = function() {
        try {
            if (request.readyState === request.DONE) {
              if (request.status === 200) {
                let response = JSON.parse(request.response);
                let messages = response["messages"];
                let contactUsername = response["contact_username"];
                let currentUsername = response["current_username"];

                const contactSearchWrapper = document.getElementById("contact-search-wrapper-id");
                const contactListWrapper = document.getElementById("contact-list-wrapper-id");
                const chatWrapper = document.getElementById("chat-wrapper-id");
                contactSearchWrapper.setAttribute("class", "col-lg-3");
                contactListWrapper.setAttribute("class", "col-lg-3");
                // chatWrapper.style.visibility = "visible";
                chatWrapper.setAttribute("class", 
                                         chatWrapper
                                         .getAttribute("class")
                                         .replace(" hidden-element", ""));
                let selectedContact = document.getElementById(contactId);
                let previousSelectedContact = document.querySelector(".selected-current-contact");
                if (!(previousSelectedContact
                    && previousSelectedContact.getAttribute("id") === contactId)) {
                          previousSelectedContact.setAttribute("class", 
                                                               previousSelectedContact
                                                              .getAttribute("class")
                                                              .replace(" selected-current-contact", ""));
                          selectedContact.setAttribute("class", 
                                                       selectedContact
                                                       .getAttribute("class") + " " + "selected-current-contact");
                          add_messages(currentUsername, contactUsername, messages);
                }
              } else {
                alert("There was a problem with the request.");
              }
            }
          }
          catch(e) {
            alert("Caught Exception: " + e.description);
          }
    }
    request.send(JSON.stringify({"contact_id": contactId}));
}


// event listeners

document.getElementById('send-message-button-id').addEventListener("click", function(){
    let selectedCurrentContact = document.querySelector(".selected-current-contact");
    if (selectedCurrentContact) {
      let recipient_id = selectedCurrentContact.getAttribute("id");
      let message_text = document.getElementById('message-field-id').value;
      send_message(recipient_id, message_text);
    }
    else {
      console.log("Can't send message: no contact is selected")
    }
});

document.getElementById("contact-list-id").addEventListener("click", function(event) {
    if (event.target.tagName.toLowerCase() === "li") {
        choose_contact(event.target.id);
    }
    else if (event.target.tagName.toLowerCase() === "span") {
        choose_contact(event.target.parentElement.id);
    }
  });

  window.addEventListener("load", scrollMessageAreaToBottom);
