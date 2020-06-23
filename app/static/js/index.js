"use strict";

// server sends numbers as strings on ajax requests

// constants
const POLLING_TIMEOUT = 3000;

const USER_PREFIX = "user-";
const CHAT_PREFIX = "chat-";
const CURRENT_SELECTED = "selected-current-chat";
const SELECTED_ELEMENT = "selected-element";
const CHECK_MESSAGE_INTERVAL = 3000;
const VISIBLE = "visible";
const HIDDEN = "hidden";
const COLLAPSED = "collapse"; 

const USER_WINDOW_ID = "user-window-id";
const USER_LIST_ID = "user-list-id";
const ADD_CONTACT_BUTTON_ID = "add-contacts-id";

const CHAT_WINDOW_ID = "chat-window-id";
const CHAT_LIST_ID = "chat-list-id";
const REMOVE_CHAT_BUTTON_ID = "remove-selected-chat-id";

const MESSAGE_WINDOW_ID = "message-window-id";
const CHAT_HEADER_ID = "chat-header-id";
const MESSAGE_AREA_ID = "message-area-id";
const MESSAGE_FIELD_ID ="message-field-id";
const MESSAGE_CLASS = "message";
const SEND_MESSAGE_BUTTON_ID = "send-message-button-id";

const JSON_CONTENT_TYPE = "application/json";


function createAlert(text) {
  let container = document.getElementById("flashed-messages");
  let messageDiv = document.createElement("div");
  messageDiv.className = "alert alert-warning";
  let closeButton = document.createElement("button");
  closeButton.className = "close";
  closeButton.setAttribute("data-dismiss", "alert");
  closeButton.innerText = "×";
  messageDiv.appendChild(closeButton);
  let textElement = document.createElement("span");
  textElement.innerText = text;
  messageDiv.appendChild(textElement);
  container.appendChild(messageDiv);
}


function logFailedAjaxRequest(request) {
  alert("There was a problem with the request.");
  console.log("There was a problem with the request.");
  console.log("Request status: " + request.status);
  console.log("Response: " + JSON.parse(request.response));
}

function logException(exception) {
  alert("Caught Exception: " + exception.description);
  console.log("Caught Exception: " + exception.description);
  console.log("Exception: " + exception);
}


// classes


class UserWindow {
  constructor(userWindowId, userListId, addContactButtonId) {
    this.USER_PREFIX = "user-";
    this.LIST_ITEM_CLASS = this.USER_PREFIX + "item";
    this.FORMAT_SPAN_CLASS = "fa-li";
    this.FORMAT_I_CLASS = "fas fa-times";
    this.users = new Set();
    this.userWindow = document.getElementById(userWindowId);
    this.userList = document.getElementById(userListId);
    this.selectedUsers = new Set();
    this.addContactButton = document.getElementById(addContactButtonId);
    this.messageWindowReference = null;
    this.chatWindowReference = null;
    this.setUsers();
  }

  setUsers() {
    for (let index = 0; index < this.userList.children.length; index++) {
      this.users.add(this.userList.children[index].id.split("-")[1]);
    }
  }

  setMessageWindowReference(messageWindowReference) {
    this.messageWindowReference = messageWindowReference;
  }

  setChatWindowReference(chatWindowReference) {
    this.chatWindowReference = chatWindowReference;
  }

  setClass(className) {
    this.userWindow.setAttribute("class", className);
  }

  getClass() {
    return this.userWindow.getAttribute("class");
  }

  updateAddContactButton() {
    console.log('hey' + this.selectedUsers.size);
    if (this.selectedUsers.size) {
      this.addContactButton.style.display = "block";
    }
    else {
      this.addContactButton.style.display = "none";
    }
  };
  
  removeUser(userId) {
    if (this.users.has(userId)) {
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

class ChatWindow {
  constructor(chatWindowId, 
              chatListId,
              removeChatButtonId) {
    this.CHAT_PREFIX = "chat-";
    this.LIST_ITEM_CLASS = this.CHAT_PREFIX + "item";
    this.FORMAT_SPAN_CLASS = "fa-li";
    this.FORMAT_I_CLASS = "fas fa-times";
    this.chats = new Set();
    this.chatWindow = document.getElementById(chatWindowId);
    this.chatList = document.getElementById(chatListId);
    this.removeChatButton = document.getElementById(removeChatButtonId);
    this.selectedChat = null;
    this.messageWindowReference = null;
    this.userWindowReference = null;

    this.setChats();
  }

  setChats() {
    for (let index = 0; index < this.chatList.children.length; index++) {
      this.chats.add(this.chatList.children[index].id.split("-")[1]);
    }
  };

  chooseChat(currentUsername, chatName, chatId, messages) {
    let lastSelected = this.selectedChat;
    this.selectedChat = document
                            .getElementById(CHAT_PREFIX
                                            + chatId);
    if (lastSelected) {
          lastSelected
          .setAttribute("class", 
                        lastSelected
                        .getAttribute("class")
                        .replace(" " + CURRENT_SELECTED, ""));
    }
    
    if (!lastSelected
        || !(lastSelected.id.split("-")[1] === chatId)) {
              this
              .selectedChat
              .setAttribute("class", 
                            (this.selectedChat
                            .getAttribute("class") 
                              + " "
                              + CURRENT_SELECTED));

              this.messageWindowReference.addMessages(currentUsername, messages);
              this.messageWindowReference.setChatHeader(chatName);
              this.messageWindowReference.show();

              this.showRemoveChatButton();
    } else {
        this.hideRemoveChatButton();
        this.messageWindowReference.hide();
        this.selectedChat = null;
    }   
  };

  chooseChatAjax(chatId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/choose_chat", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    let thisReference = this;

    request.onload = (function() {
        try {
            if (request.readyState === request.DONE) {
              if (request.status === 200) {
                const response = JSON.parse(request.response);
                const messages = response["messages"];
                const chatName = response["chat_name"];
                const currentUsername = response["current_username"];

                thisReference.chooseChat(currentUsername, chatName, 
                                         chatId, messages);
              } else {
                logFailedAjaxRequest(request);
              }
            }
          }
          catch(e) {
            logException(e);
          }
    }).bind(this);
    request.send(JSON.stringify({"chat_id": chatId}));
  };
///////////

  addChat(chatName, chatId) {
    if (!this.chats.has(chatId)) {
      let listItem = document.createElement("li");
      let formatSpan = document.createElement("span");
      let chatNameSpan = document.createElement("span");
      let formatI = document.createElement("i");
      listItem.id = this.CHAT_PREFIX + chatId;
      listItem.className = this.LIST_ITEM_CLASS;
      formatSpan.setAttribute("class", this.FORMAT_SPAN_CLASS);
      formatI.setAttribute("class", this.FORMAT_I_CLASS);
      chatNameSpan.innerText = " " + chatName;
      formatSpan.appendChild(formatI);
      listItem.appendChild(formatSpan);
      this.chats = new Set();
      this.chats.add(chatId);

      // if (this
      //     .chatWindow
      //     .selectedChat && this
      //                     .chatWindow
      //                     .selectedChat.id.split("-")[1] === chatId) {
      //   listItem.setAttribute("class", 
      //                         this.LIST_ITEM_CLASS + " " + SELECTED_ELEMENT);
      //   this.chatWindow.selectedChat = listItem;
      // }
      // else {
      //   listItem.setAttribute("class",
      //                         this.LIST_ITEM_CLASS);
      // }
      listItem.appendChild(chatNameSpan);
      // this.chatList.innerText = "";  
      this.chatList.appendChild(listItem);
    }
  };

  addChats(addedChats) {
    for (let index = 0; index < addedChats.length; index++) {
      const chat = addedChats[index];
      const chatName = chat["chat_name"];
      const chatId = chat["chat_id"];
      this.addChat(chatName, chatId);
    }
    this.userWindowReference.updateAddContactButton();
  };

  addContactsAndChatsAjax(userIds) {
    if (this.userWindowReference.selectedUsers.size) {
      let request = new XMLHttpRequest();
      request.open("POST", "/add_contacts_and_chats", true);
      request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

      let thisReference = this;

      request.onload = function() {
        try {
          if (request.readyState === request.DONE) {
            if (request.status === 200) {
              const response = JSON.parse(request.response);
              const addedChats = response["added_chats"];
              thisReference.addChats(addedChats);
            } else {
              logFailedAjaxRequest(request);
            }
          }
        }
        catch(e) {
          logException(e);
        }
      }
      request.send(JSON.stringify({user_ids: userIds}))
    }
  };

  setClass(className) {
    this.chatWindow.setAttribute("class", className);
  };

  getClass() {
    return this.chatWindow.getAttribute("class");
  };

  setMessageWindowReference(messageWindowReference) {
    this.messageWindowReference = messageWindowReference;
  };

  setUserWindowReference(userWindowReference) {
    this.userWindowReference = userWindowReference;
  };

  showRemoveChatButton() {
    this.removeChatButton.style.display = "block";
  };

  hideRemoveChatButton() {
    this.removeChatButton.style.display = "none";
  };

  removeChat(chatId) {
    console.log('hey' + this.chats)
    if (this.chats.has(chatId)) {
      
        const listItem = document.getElementById(this.CHAT_PREFIX + chatId);
        this.chatList.removeChild(listItem);
        this.chats.delete(chatId);
        this.selectedChat = null;
        this.hideRemoveChatButton();
        this.messageWindowReference.hide();
    }
  };

  removeChatAjax(chatId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/remove_chat", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    let thisReference = this;

    request.onload = function() {
      try {
        if (request.readyState === request.DONE) {
          if (request.status === 200) {
            const response = JSON.parse(request.response);
            const chat = response["removed_chat"];
            const chatId = chat["chat_id"];
            thisReference.removeChat(chatId);
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
    request.send(JSON.stringify({chat_id: chatId}))
  };
}

class MessageWindow {
  constructor(messageWindowId, messageAreaId,
              messageFieldId, sendMessageButtonId, chatHeaderId) {
    this.COLUMN_3 = "col-lg-3";
    this.CENTER_FROM_LEFT = "center-from-left";
    this.CENTER_FROM_RIGHT = "center-from-right";
    this.messageWindow = document.getElementById(messageWindowId);
    this.chatHeader = document.getElementById(chatHeaderId);
    this.messageArea =  document.getElementById(messageAreaId);
    this.messageField = document.getElementById(messageFieldId);
    this.sendMessageButton = document.getElementById(sendMessageButtonId);
    this.chatWindowReference = null;
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
                                          .chatWindowReference
                                          .selectedChat
                                          .id
                                          .split("-")[1]
    );
  };

  stopMessagePolling() {
    clearInterval(this.setIntervalHandle);
    this.setIntervalHandle = null;
  };

  setChatHeader(header) {
    this.chatHeader.innerText = header;
  };

  addMessage(currentUsername, message) {
    const text = message["text"];

    const dateCreated = message["date_created"];
    let sender_username = message["sender_username"];
    let username;
    if (sender_username === currentUsername) {
        username = "You";
    }
    else {
        username = sender_username;
    }
    let messageDiv = document.createElement("div");
    let messageSpan = document.createElement("span");
    let dateCreatedSpan = document.createElement("span");
    let textSpan = document.createElement("span");
    const b = document.createElement("b");
    const br = document.createElement("br");
    b.innerText = username + " ";
    textSpan.innerText = text;
    dateCreatedSpan.innerText = dateCreated + "\n";
    messageSpan.appendChild(b);
    messageSpan.appendChild(dateCreatedSpan);
    messageSpan.appendChild(br);
  
    messageDiv.appendChild(messageSpan);
    messageDiv.appendChild(br);
    messageDiv.appendChild(textSpan);
    messageDiv.setAttribute("class", "message");
    
    this.messageArea.appendChild(messageDiv);
    this.messageArea.appendChild(br);
    this.scrollDown();
  };

  addMessages(currentUsername, messages, clearArea = true) {
    if (clearArea) {
      this.messageArea.innerHTML = "";
    }
    
    for (let index = 0; index < messages.length; index++) {
        const message = messages[index];
        this.addMessage(currentUsername, message);
    }
  };

  checkNewMessagesAjax(currentChatId) {
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
              const currentUsername = response["current_username"];
              thisReference.addMessages(currentUsername,
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
                   chat_id: currentChatId
                 };
    request.send(JSON.stringify(data));
  };


  sendMessageAjax(chatId, messageText){
    const text = messageText.trim();
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
                    const chatName = response["chat_name"];
                    const currentUsername = response["current_username"];

                    thisReference.messageField.value = "";
                    
                    thisReference.addMessage(currentUsername, message);
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
                      chat_id: chatId
                   };
        request.send(JSON.stringify(data));
    }
  };

  setChatWindowReference(chatWindowReference) {
    this.chatWindowReference = chatWindowReference;
  };

  setUserWindowReference(userWindowReference) {
    this.userWindowReference = userWindowReference;
  };
  
  getClass() {
    this.messageWindow.getAttribute("class");
  };

  setClass(className) {
    this.messageWindow.setAttribute("class", className);
  };

  addClass(className) {
    this.messageWindow.setAttribute("class",
                           this.getClass() + " " + className);
  };

  removeClass(className) {
    this.messageWindow.setAttribute("class", 
                                 this.getClass()
                                     .replace(" " + className, ""));
  };

  scrollDown() {
    this.messageArea.scrollTo(0, this.messageArea.scrollHeight);
  };

  show() {
    this.startMessagePolling();
    this.messageWindow.style.display = "block";
    this.userWindowReference.setClass(this.COLUMN_3);
    this.chatWindowReference.setClass(this.COLUMN_3);
  };

  hide() {
    this.stopMessagePolling();
    this.messageWindow.style.display = "none";
    this.userWindowReference.setClass(this.COLUMN_3
                                      + " " + this.CENTER_FROM_LEFT);
    this.chatWindowReference.setClass(this.COLUMN_3 
                                         + " " + this.CENTER_FROM_RIGHT);
  };
}

/* ----------------
driver
-----------------*/

let messageWindow = new MessageWindow(MESSAGE_WINDOW_ID, 
                                      MESSAGE_AREA_ID, MESSAGE_FIELD_ID,
                                      SEND_MESSAGE_BUTTON_ID, CHAT_HEADER_ID);
let userWindow = new UserWindow(USER_WINDOW_ID,
                                USER_LIST_ID,
                                ADD_CONTACT_BUTTON_ID);
let chatWindow = new ChatWindow(CHAT_WINDOW_ID,
                                CHAT_LIST_ID,
                                REMOVE_CHAT_BUTTON_ID);

messageWindow.setChatWindowReference(chatWindow);
messageWindow.setUserWindowReference(userWindow);
userWindow.setChatWindowReference(chatWindow);
userWindow.setMessageWindowReference(messageWindow);
chatWindow.setUserWindowReference(userWindow);
chatWindow.setMessageWindowReference(messageWindow);

userWindow
.addContactButton
.addEventListener("click", function () {
    chatWindow.addContactsAndChatsAjax(Array.from(userWindow.selectedUsers));
});

chatWindow
.removeChatButton
.addEventListener("click", function() {
    if (chatWindow.selectedChat) {
        chatWindow.removeChatAjax(chatWindow
                                  .selectedChat
                                  .id
                                  .split("-")[1]);
    }
});

messageWindow
.sendMessageButton
.addEventListener("click", function(){
    if (chatWindow.selectedChat) {
        const chatId = chatWindow.selectedChat.id.split("-")[1];
        const messageText = messageWindow.messageField.value;
        messageWindow.sendMessageAjax(chatId, messageText);
    }
    else {
          console.log("Can't send the message: no contact selected");
    }
});


chatWindow
.chatList
.addEventListener("click", function(event) {
    if (event.target.tagName.toLowerCase() === "li") {
        const elementId = event.target.id.split("-")[1];
        chatWindow.chooseChatAjax(elementId);
    }
    else if (event.target.tagName.toLowerCase() === "span") {
        const elementId = event.target.parentElement.id.split("-")[1];
        chatWindow.chooseChatAjax(elementId);
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
    userWindow.updateAddContactButton();
});

window
.addEventListener("load", function() {
    messageWindow.scrollDown();

    chatWindow
    .selectedChat = document.querySelector("." + CURRENT_SELECTED);
    
    if (chatWindow.selectedChat) {
      chatWindow.showRemoveChatButton();
      messageWindow.startMessagePolling();
    }
});
