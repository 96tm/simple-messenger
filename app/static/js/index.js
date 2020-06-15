"use strict";

// server sends numbers as strings on ajax requests

// constants
const POLLING_TIMEOUT = 3000;

const USER_PREFIX = "user-";
const CONTACT_PREFIX = "contact-";
const CURRENT_SELECTED = "selected-current-contact";
const SELECTED_ELEMENT = "selected-element";
const CHECK_MESSAGE_INTERVAL = 3000;
const VISIBLE = "visible";
const HIDDEN = "hidden";
const COLLAPSED = "collapse"; 

const USER_WINDOW_ID = "user-window-id";
const USER_LIST_ID = "user-list-id";
const ADD_USER_BUTTON_ID = "add-selected-contacts-id";

const CONTACT_WINDOW_ID = "contact-window-id";
const CONTACT_LIST_ID = "contact-list-id";
const REMOVE_CONTACT_BUTTON_ID = "remove-selected-contact-id";

const CHAT_WINDOW_ID = "chat-window-id";
const CHAT_HEADER_ID = "chat-header-id";
const MESSAGE_AREA_ID = "message-area-id";
const MESSAGE_FIELD_ID ="message-field-id";
const MESSAGE_CLASS = "message";
const SEND_MESSAGE_BUTTON_ID = "send-message-button-id";

const JSON_CONTENT_TYPE = "application/json";


function logFailedAjaxRequest(request) {
  alert("There was a problem with the request.");
  console.log("There was a problem with the request.");
  console.log("Request status: " + request.status);
  console.log("Response: " + JSON.parse(request.response));
}

function logException(exception) {
  alert("Caught Exception: " + e.description);
  console.log("Caught Exception: " + e.description);
  console.log("Exception: " + e);
}


// classes


class UserWindow {
  constructor(userWindowId, userListId, addUserButtonId) {
    this.USER_PREFIX = "user-";
    this.LIST_ITEM_CLASS = this.USER_PREFIX + "item";
    this.FORMAT_SPAN_CLASS = "fa-li";
    this.FORMAT_I_CLASS = "fas fa-times";
    this.users = new Set();
    this.userWindow = document.getElementById(userWindowId);
    this.userList = document.getElementById(userListId);
    this.selectedUsers = new Set();
    this.addUserButton = document.getElementById(addUserButtonId);
    this.chatWindowReference = null;
    this.contactWindowReference = null;
    this.setUsers();
  }

  setUsers() {
    for (let index = 0; index < this.userList.children.length; index++) {
      this.users.add(this.userList.children[index].id.split("-")[1]);
    }
  }

  setChatWindowReference(chatWindowReference) {
    this.chatWindowReference = chatWindowReference;
  }

  setContactWindowReference(contactWindowReference) {
    this.contactWindowReference = contactWindowReference;
  }

  setClass(className) {
    this.userWindow.setAttribute("class", className);
  }

  getClass() {
    return this.userWindow.getAttribute("class");
  }

  updateAddUserButton() {
    if (this.selectedUsers.size) {
      this.addUserButton.style.visibility = VISIBLE;
    }
    else {
      this.addUserButton.style.visibility = HIDDEN;
    }
  };
  
  removeUser(userId) {
    if (this.users.has(userId)) { // INT OR STRING?
        const listItem = document.getElementById(this.USER_PREFIX + userId);
        this.userList.removeChild(listItem);
        this.users.delete(userId);
        this.selectedUsers.delete(userId);
    }
  };

  addUser(username, userId) {
    if (!this.users.has(userId)) {
        let listItem = document.createElement("li");
        let formatSpan = document.createElement("span");
        let usernameSpan = document.createElement("span");
        let formatI = document.createElement("i");
        listItem.setAttribute("class", this.LIST_ITEM_CLASS);
        listItem.id = this.USER_PREFIX + userId;
        formatSpan.setAttribute("class", this.FORMAT_SPAN_CLASS);
        formatI.setAttribute("class", this.FORMAT_I_CLASS);
        usernameSpan.innerText = username;
        formatSpan.appendChild(formatI);
        listItem.appendChild(formatSpan);
        listItem.appendChild(usernameSpan);
        this.userList.appendChild(listItem);

        this.users.add(userId);
    }
  };
}

class ContactWindow {
  constructor(contactWindowId, 
              contactListId,
              removeContactButtonId) {
    this.CONTACT_PREFIX = "contact-";
    this.LIST_ITEM_CLASS = this.CONTACT_PREFIX + "item";
    this.FORMAT_SPAN_CLASS = "fa-li";
    this.FORMAT_I_CLASS = "fas fa-times";
    this.contacts = new Set();
    this.contactWindow = document.getElementById(contactWindowId);
    this.contactList = document.getElementById(contactListId);
    this.removeContactButton = document.getElementById(removeContactButtonId);
    this.selectedContact = null;
    this.chatWindowReference = null;
    this.userWindowReference = null;

    this.setContacts();
  }

  setContacts() {
    for (let index = 0; index < this.contactList.children.length; index++) {
      this.contacts.add(this.contactList.children[index].id.split("-")[1]);
    }
  };

  chooseContact(currentUsername, contactUsername, contactId, messages) {
    let lastSelected = this.selectedContact;
    this.selectedContact = document
                            .getElementById(CONTACT_PREFIX
                                            + contactId);
    if (lastSelected) {
          lastSelected
          .setAttribute("class", 
                        lastSelected
                        .getAttribute("class")
                        .replace(" " + CURRENT_SELECTED, ""));
    }
    
    if (!lastSelected
        || !(lastSelected.id.split("-")[1] === contactId)) {
              this
              .selectedContact
              .setAttribute("class", 
                            (this.selectedContact
                            .getAttribute("class") 
                              + " "
                              + CURRENT_SELECTED));
              this.chatWindowReference.addMessages(currentUsername, contactUsername, messages);
              this.chatWindowReference.setChatHeader(contactUsername);
              this.chatWindowReference.show();

              this.showRemoveContactButton();
    } else {
        this.hideRemoveContactButton();
        this.chatWindowReference.hide();
        this.selectedContact = null;
    }   
  };

  choose_contact(contactId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/choose_contact", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    let thisReference = this;

    request.onload = (function() {
        try {
            if (request.readyState === request.DONE) {
              if (request.status === 200) {
                const response = JSON.parse(request.response);
                const messages = response["messages"];
                const contactUsername = response["contact_username"];
                const currentUsername = response["current_username"];
                thisReference.chooseContact(currentUsername, contactUsername, contactId, messages);
              } else {
                logFailedAjaxRequest(request);
              }
            }
          }
          catch(e) {
            logException(e);
          }
    }).bind(this);
    request.send(JSON.stringify({"contact_id": contactId}));
  };

  addContact(username, contactId) {
    if (!this.contacts.has(contactId)) { // INT OR STRING?
        let listItem = document.createElement("li");
        let formatSpan = document.createElement("span");
        let usernameSpan = document.createElement("span");
        let formatI = document.createElement("i");
        listItem.setAttribute("class", this.LIST_ITEM_CLASS);
        listItem.id = this.CONTACT_PREFIX + contactId;
        formatSpan.setAttribute("class", this.FORMAT_SPAN_CLASS);
        formatI.setAttribute("class", this.FORMAT_I_CLASS);
        usernameSpan.innerText = " " + username;
        formatSpan.appendChild(formatI);
        listItem.appendChild(formatSpan);
        this.contacts.add(contactId); // INT OF STRING?
        
        listItem.appendChild(usernameSpan);
        this.contactList.appendChild(listItem);

        this.userWindowReference.removeUser(contactId);
    }
  };

  addContacts(addedContacts) {
    for (let index = 0; index < addedContacts.length; index++) {
      const contact = addedContacts[index];
      const username = contact["username"];
      const contactId = contact["contact_id"];
      this.addContact(username, contactId);
    }
    this.userWindowReference.updateAddUserButton();
  };

  add_contacts(contactIds) {
    if (this.userWindowReference.selectedUsers.size) {
      let request = new XMLHttpRequest();
      request.open("POST", "/add_contacts", true);
      request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

      let thisReference = this;

      request.onload = function() {
        try {
          if (request.readyState === request.DONE) {
            if (request.status === 200) {
              const response = JSON.parse(request.response);
              const addedContacts = response["added_contacts"];
              thisReference.addContacts(addedContacts);
            } else {
              logFailedAjaxRequest(request);
            }
          }
        }
        catch(e) {
          logException(e);
        }
      }
      request.send(JSON.stringify({contact_ids: contactIds}))
    }
  };

  setClass(className) {
    this.contactWindow.setAttribute("class", className);
  };

  getClass() {
    return this.contactWindow.getAttribute("class");
  };

  setChatWindowReference(chatWindowReference) {
    this.chatWindowReference = chatWindowReference;
  };

  setUserWindowReference(userWindowReference) {
    this.userWindowReference = userWindowReference;
  };

  showRemoveContactButton() {
    this.removeContactButton.style.visibility = VISIBLE;
  };

  hideRemoveContactButton() {
    this.removeContactButton.style.visibility = HIDDEN;
  };

  removeContact(username, contactId) {
    if (this.contacts.has(contactId)) {

        const listItem = document.getElementById(this.CONTACT_PREFIX + contactId);
        
        this.contactList.removeChild(listItem);
        this.contacts.delete(contactId); // INT OR STRING?
        this.selectedContact = null;
        this.hideRemoveContactButton();

        this.userWindowReference.addUser(username, contactId);
        this.chatWindowReference.hide();
    }
  };

  remove_contact(contactId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/remove_contact", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    let thisReference = this;

    request.onload = function() {
      try {
        if (request.readyState === request.DONE) {
          if (request.status === 200) {
            const response = JSON.parse(request.response);
            const contact = response["removed_contact"];
            const contactId = contact["contact_id"];
            const username = contact["username"];
  
            thisReference.removeContact(username, contactId);
          }
          else {
            logFailedAjaxRequest(request);
          }
        }
      }
      catch(e) {
        logException(e);
      }
    }
    request.send(JSON.stringify({contact_id: contactId}))
  };
}

class ChatWindow {
  constructor(chatWindowId, messageAreaId,
              messageFieldId, sendMessageButtonId, chatHeaderId) {
    this.COLUMN_3 = "col-lg-3";
    this.CENTER_FROM_LEFT = "center-from-left";
    this.CENTER_FROM_RIGHT = "center-from-right";
    this.CHAT_HEADER_PREFIX = "Chat with ";
    this.chatWindow = document.getElementById(chatWindowId);
    this.chatHeader = document.getElementById(chatHeaderId);
    this.messageArea =  document.getElementById(messageAreaId);
    this.messageField = document.getElementById(messageFieldId);
    this.sendMessageButton = document.getElementById(sendMessageButtonId);
    this.contactWindowReference = null;
    this.userWindowReference = null;
    this.setIntervalHandle = null;
  }

  startMessagePolling() {
    let thisReference = this;
    this.setIntervalHandle = window
                             .setInterval(this
                                          .checkNewMessagesAjax
                                          .bind(thisReference),
                                          POLLING_TIMEOUT,
                                          this
                                          .contactWindowReference
                                          .selectedContact
                                          .id
                                          .split("-")[1]
    );
  };

  stopMessagePolling() {
    clearInterval(this.setIntervalHandle);
    this.setIntervalHandle = null;
  };

  setChatHeader(header) {
    this.chatHeader.innerText = this.CHAT_HEADER_PREFIX + header;
  };

  addMessage(currentUsername, contactUsername, message) {
    const text = message["text"];

    const timestamp = message["timestamp"];
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
    const b = document.createElement("b");
    const br = document.createElement("br");
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
    
    this.messageArea.appendChild(messageDiv);
    this.messageArea.appendChild(br);
    this.scrollDown();
  };

  addMessages(currentUsername, contactUsername, messages, clearArea = true) {
    if (clearArea) {
      this.messageArea.innerHTML = "";
    }
    
    for (let index = 0; index < messages.length; index++) {
        const message = messages[index];
        this.addMessage(currentUsername, contactUsername, message);
    }
  };


  checkNewMessagesAjax(currentContactId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/check_new_messages", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    let thisReference = this;

    request.onload = function(){
      try {
          if (request.readyState === request.DONE) {
            if (request.status === 200) {
              const response = JSON.parse(request.response);
              const messages = response["messages"];
              const contactUsername = response["contact_username"];
              const currentUsername = response["current_username"];
              thisReference.addMessages(currentUsername,
                                         contactUsername,
                                         messages, false);
            } else {
              logFailedAjaxRequest(request);
            }
          }
        }
        catch(e) {
          logException(e);
        }
    }
    const data = {
                   contact_id: currentContactId
                 };
    request.send(JSON.stringify(data));
  };


  send_message(recipient_id, message_text){
    const text = message_text.trim();
    if (text) {
        let request = new XMLHttpRequest();
        request.open("POST", "/send_message", true);
        request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

        let thisReference = this;

        request.onload = function(){
            try {
                if (request.readyState === request.DONE) {
                  if (request.status === 200) {
                    const response = JSON.parse(request.response);
                    const message = response["message"];
                    const contactUsername = response["contact_username"];
                    const currentUsername = response["current_username"];

                    thisReference.messageField.value = "";
                    
                    thisReference.addMessage(currentUsername,
                                     contactUsername, message);
                  } else {
                    logFailedAjaxRequest(request);
                  }
                }
              }
              catch(e) {
                logException(e);
              }
        }
        let data = {
                        message: text,
                        recipient_id: recipient_id
                   };
        request.send(JSON.stringify(data));
    }
  };

  setContactWindowReference(contactWindowReference) {
    this.contactWindowReference = contactWindowReference;
  };

  setUserWindowReference(userWindowReference) {
    this.userWindowReference = userWindowReference;
  };
  
  getClass() {
    this.chatWindow.getAttribute("class");
  };

  setClass(className) {
    this.chatWindow.setAttribute("class", className);
  };

  addClass(className) {
    this.chatWindow.setAttribute("class",
                           this.getClass() + " " + className);
  };

  removeClass(className) {
    this.chatWindow.setAttribute("class", 
                                 this.getClass()
                                     .replace(" " + className, ""));
  };

  scrollDown() {
    this.messageArea.scrollTo(0, this.messageArea.scrollHeight);
  };

  show() {
    this.startMessagePolling();
    this.chatWindow.style.display = "block";
    this.userWindowReference.setClass(this.COLUMN_3);
    this.contactWindowReference.setClass(this.COLUMN_3);
  };

  hide() {
    this.stopMessagePolling();
    this.chatWindow.style.display = "none";
    this.userWindowReference.setClass(this.COLUMN_3
                                      + " " + this.CENTER_FROM_LEFT);
    this.contactWindowReference.setClass(this.COLUMN_3 
                                         + " " + this.CENTER_FROM_RIGHT);
  };
}

/* ----------------
driver
-----------------*/

let chatWindow = new ChatWindow(CHAT_WINDOW_ID, 
                                MESSAGE_AREA_ID, MESSAGE_FIELD_ID,
                                SEND_MESSAGE_BUTTON_ID, CHAT_HEADER_ID);
let userWindow = new UserWindow(USER_WINDOW_ID,
                            USER_LIST_ID,
                            ADD_USER_BUTTON_ID);
let contactWindow = new ContactWindow(CONTACT_WINDOW_ID,
                                  CONTACT_LIST_ID,
                                  REMOVE_CONTACT_BUTTON_ID);

chatWindow.setContactWindowReference(contactWindow);
chatWindow.setUserWindowReference(userWindow);
userWindow.setContactWindowReference(contactWindow);
userWindow.setChatWindowReference(chatWindow);
contactWindow.setUserWindowReference(userWindow);
contactWindow.setChatWindowReference(chatWindow);

userWindow
.addUserButton
.addEventListener("click", function () {
    contactWindow.add_contacts(Array.from(userWindow.selectedUsers));
});

contactWindow
.removeContactButton
.addEventListener("click", function() {
    if (contactWindow.selectedContact) {
        contactWindow.remove_contact(contactWindow
                                      .selectedContact
                                      .id
                                      .split("-")[1]);
    }
});

chatWindow
.sendMessageButton
.addEventListener("click", function(){
    if (contactWindow.selectedContact) {
        const recipient_id = contactWindow.selectedContact.id.split("-")[1];
        const message_text = chatWindow.messageField.value;
        chatWindow.send_message(recipient_id, message_text);
    }
    else {
          console.log("Can't send the message: no contact selected");
    }
});


contactWindow
.contactList
.addEventListener("click", function(event) {
    if (event.target.tagName.toLowerCase() === "li") {
        const elementId = event.target.id.split("-")[1];
        contactWindow.choose_contact(elementId);
    }
    else if (event.target.tagName.toLowerCase() === "span") {
        const parentElementId = event.target.parentElement.id.split("-")[1];
        contactWindow.choose_contact(parentElementId);
    }
});

userWindow
.userList
.addEventListener("click", function(event) {
    const item = event.target;
    if (item.tagName.toLowerCase() === "li") {
        const itemClass = item.getAttribute("class");
        const itemId = item.id.split("-")[1];
        if (itemClass.includes(SELECTED_ELEMENT)) {
            userWindow.selectedUsers.delete(itemId);
            item.setAttribute("class", 
                                itemClass
                                .replace(" " + SELECTED_ELEMENT, ""));
        }
        else {
            userWindow.selectedUsers.add(itemId);
            item.setAttribute("class", itemClass + " " + SELECTED_ELEMENT);
        }
    }
    else if (item.tagName.toLowerCase() === "span") {
        const parent = item.parentElement;
        const itemParentClass = parent.getAttribute("class");
        const itemParentId = parent.id.split("-")[1];
        if (itemParentClass.includes(SELECTED_ELEMENT)) {
            userWindow.selectedUsers.delete(itemParentId);
            parent.setAttribute("class", 
                                itemParentClass
                                .replace(" " + SELECTED_ELEMENT, ""));
        }
        else {
            userWindow.selectedUsers.add(itemParentId);
            parent.setAttribute("class", 
                                itemParentClass + " " + SELECTED_ELEMENT);
        }
    }
    userWindow.updateAddUserButton();
});

window
.addEventListener("load", function() {
    chatWindow.scrollDown();

    contactWindow
    .selectedContact = document.querySelector("." + CURRENT_SELECTED);
    
    if (contactWindow.selectedContact) {
      contactWindow.showRemoveContactButton();
      chatWindow.startMessagePolling();
    }
});
