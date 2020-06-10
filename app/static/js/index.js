// globals
let selectedUsers = new Set();
const USER_PREFIX = "user-";
const CONTACT_PREFIX = "contact-";
const CURRENT_SELECTED = "selected-current-contact";
const HIDDEN = "hidden-element";
const CHECK_MESSAGE_INTERVAL = 3000;


//

function checkNewMessages(lastTimestamp) {
  // TODO
}

function hideRemoveContactButton() {
  button = document.getElementById("remove-selected-contact-id");
  button.style.visibility = "hidden"
}

function showRemoveContactButton() {
  button = document.getElementById("remove-selected-contact-id");
  button.style.visibility = "visible"
}


function showChat() {
  chat = document.getElementById("chat-wrapper-id");
  chat.setAttribute("class", 
                    chat
                    .getAttribute("class")
                    .replace(" " + HIDDEN, ""));
  usersDiv = document.getElementById("contact-search-wrapper-id");
  contactsDiv = document.getElementById("contact-list-wrapper-id");
  usersDiv.setAttribute("class", "col-lg-3");
  contactsDiv.setAttribute("class", "col-lg-3");
}


function hideChat() {
  chat = document.getElementById("chat-wrapper-id");
  chat.setAttribute("class", 
                    chat
                    .getAttribute("class") + " " + HIDDEN);
  usersDiv = document.getElementById("contact-search-wrapper-id");
  contactsDiv = document.getElementById("contact-list-wrapper-id");
  usersDiv.setAttribute("class", "col-lg-6");
  contactsDiv.setAttribute("class", "col-lg-6");
}


function addUser(container, username, userId, prefix){
  let listItem = document.createElement("li");
  let formatSpan = document.createElement("span");
  let usernameSpan = document.createElement("span");
  let formatI = document.createElement("i");
  listItem.setAttribute("class", prefix + "item");
  listItem.id = prefix + userId;
  formatSpan.setAttribute("class", "fa-li");
  formatI.setAttribute("class", "fas fa-times");
  usernameSpan.innerText = username;
  formatSpan.appendChild(formatI);
  listItem.appendChild(formatSpan);
  
  listItem.appendChild(usernameSpan);
  container.appendChild(listItem);
}


function updateAddContactButton() {
  const buttonAdd = document
                    .getElementById("add-selected-contacts-id");
  if (selectedUsers.size) {
    buttonAdd.style.visibility = "visible";
  }
  else {
    buttonAdd.style.visibility = "hidden";
  }
}


function removeUser(container, userId, prefix) {
  listItem = document.querySelector("#" + prefix + userId);
  container.removeChild(listItem);
}


function remove_contact(contactId) {
  request = new XMLHttpRequest();
  request.open("POST", "/remove_contact", true);
  request.setRequestHeader("Content-Type", "application/json");
  request.onload = function() {
    try {
      if (request.readyState === request.DONE) {
        if (request.status === 200) {
          let response = JSON.parse(request.response);
          let contact = response["removed_contact"];
          let contactId = contact["contact_id"];
          let username = contact["username"];
          let userList = document.getElementById("user-list-id");
          let contactList = document.getElementById("contact-list-id");

          hideRemoveContactButton();
          hideChat();
          addUser(userList, username, contactId, USER_PREFIX);
          removeUser(contactList, contactId, CONTACT_PREFIX);
        }
        else {
          alert('There was a problem with the request.');
        }
      }
    }
    catch(e) {
      alert('Caught Exception: ' + e.description);
      console.log('Caught Exception: ' + e.description);
    }
  }
  request.send(JSON.stringify({contact_id: contactId}))
}


function add_contacts(contactIds) {
  if (selectedUsers.size) {
    request = new XMLHttpRequest();
    request.open("POST", "/add_contacts", true);
    request.setRequestHeader("Content-Type", "application/json");
    request.onload = function() {
      try {
        if (request.readyState === request.DONE) {
          if (request.status === 200) {

            let response = JSON.parse(request.response);
            let addedContacts = response["added_contacts"];
            for (index = 0; index < addedContacts.length; index++) {
              let contact = addedContacts[index];
              let username = contact["username"];
              let contactId = String(contact["contact_id"]);
              let userList = document.getElementById("user-list-id");
              let contactList = document.getElementById("contact-list-id");
              addUser(contactList, username, contactId, CONTACT_PREFIX);
              removeUser(userList, contactId, USER_PREFIX);
              selectedUsers.delete(contactId);
              updateAddContactButton();
            }
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
    request.send(JSON.stringify({contact_ids: contactIds}))
  }
}

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
                    let messageArea = document
                                      .getElementById("message-area-id");
                    document.getElementById("message-field-id").value = "";
                    add_message(messageArea, currentUsername, 
                                contactUsername, message);
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
                let contactsDiv;
                contactsDiv = document
                              .getElementById("contact-search-wrapper-id");
                let contactList;
                contactList = document
                              .getElementById("contact-list-wrapper-id");
                const chatWrapper = document
                                    .getElementById("chat-wrapper-id");
                contactsDiv.setAttribute("class", "col-lg-3");
                contactList.setAttribute("class", "col-lg-3");
                chatWrapper.setAttribute("class", 
                                         chatWrapper
                                         .getAttribute("class")
                                         .replace(" hidden-element", ""));
                let selectedContact = document
                                      .getElementById("contact-" + contactId);
                let lastSelected;
                lastSelected = document
                               .querySelector("." + CURRENT_SELECTED);
                if (lastSelected) {
                      lastSelected
                      .setAttribute("class", 
                                    lastSelected
                                    .getAttribute("class")
                                    .replace(" " + CURRENT_SELECTED, ""));
                }
                
                if (!lastSelected
                    || !(lastSelected.id.split("-")[1] === contactId)) {
                          selectedContact
                          .setAttribute("class", 
                                        (selectedContact
                                        .getAttribute("class") 
                                         + " " 
                                         + CURRENT_SELECTED));
                          add_messages(currentUsername,
                                       contactUsername, messages);
                          showChat();
                          showRemoveContactButton();
                } else {
                  hideChat();
                  hideRemoveContactButton();
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

document
.getElementById("add-selected-contacts-id")
.addEventListener("click", function () {
    add_contacts(Array.from(selectedUsers));
});

document
.getElementById("send-message-button-id")
.addEventListener("click", function(){
    const selectedCurrentContact = document
                                   .querySelector("." + CURRENT_SELECTED);
    if (selectedCurrentContact) {
      const recipient_id = selectedCurrentContact.id.split("-")[1];
      const message_text = document
                           .getElementById('message-field-id').value;
      send_message(recipient_id, message_text);
    }
    else {
      console.log("Can't send message: no contact is selected");
    }
});


document
.getElementById("contact-list-id")
.addEventListener("click", function(event) {
    if (event.target.tagName.toLowerCase() === "li") {
        elementId = event.target.id.split("-")[1];
        choose_contact(elementId);
    }
    else if (event.target.tagName.toLowerCase() === "span") {
        parentElementId = event.target.parentElement.id.split("-")[1];
        choose_contact(parentElementId);
    }
  });


document
.getElementById("user-list-id")
.addEventListener("click", function(event) {
  const item = event.target;
  if (item.tagName.toLowerCase() === "li") {
    const itemClass = item.getAttribute("class");
    const itemId = item.id.split("-")[1];
    if (itemClass.includes("selected-element")) {
          selectedUsers.delete(itemId);
          item.setAttribute("class", 
                            itemClass
                            .replace(" selected-element", ""));
    }
    else {
          selectedUsers.add(itemId);
          item.setAttribute("class", itemClass + " selected-element");
    }
  }
  else if (item.tagName.toLowerCase() === "span") {
    const parent = item.parentElement;
    const itemParentClass = parent.getAttribute("class");
    const itemParentId = parent.id.split("-")[1];
    if (itemParentClass.includes("selected-element")) {
          selectedUsers.delete(itemParentId);
          parent.setAttribute("class", 
                              itemParentClass
                              .replace(" selected-element", ""));
    }
    else {
          selectedUsers.add(itemParentId);
          parent.setAttribute("class", 
                              itemParentClass + " selected-element");
    }
  }
  updateAddContactButton();
});

document
.getElementById("remove-selected-contact-id")
.addEventListener("click", function() {
  selected = document.querySelector("." + CURRENT_SELECTED);
  if (selected) {
    remove_contact(selected.id.split("-")[1]);
  }
});

window
.addEventListener("load", function() {
  scrollMessageAreaToBottom();
  console.log('selected here' + Boolean(document.querySelector("." + CURRENT_SELECTED)));
  if (document.querySelector("." + CURRENT_SELECTED)) {
    showRemoveContactButton();
  }
});



