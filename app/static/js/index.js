"use strict";


// server sends numbers as strings on ajax requests
// assume moment.js is loaded


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
const USER_SEARCH_ID = "user-search-id";
const ADD_CONTACT_BUTTON_ID = "add-contacts-id";

const CHAT_WINDOW_ID = "chat-window-id";
const CHAT_LIST_ID = "chat-list-id";
const CHAT_SEARCH_INPUT_ID = "chat-search-id";
const REMOVE_CHAT_BUTTON_ID = "remove-selected-chat-id";

const MESSAGE_WINDOW_ID = "message-window-id";
const CHAT_HEADER_ID = "chat-header-id";
const MESSAGE_AREA_ID = "message-area-id";
const MESSAGE_FIELD_ID ="message-field-id";
const MESSAGE_CLASS = "message";
const SEND_MESSAGE_BUTTON_ID = "send-message-button-id";

const JSON_CONTENT_TYPE = "application/json";


// utility functions
function format_date(date) {
  const format_string = "MMMM Do YYYY, h:mm:ss a";
  return moment(date).format(format_string);
}


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
  console.log("There was a problem with the request.");
  console.log("Request status: " + request.status);
  console.log("Response: " + JSON.parse(request.response));
}


function logException(exception) {
  console.log("Caught Exception: " + exception.description);
  console.log("Exception: " + exception);
}


// classes
class UserWindow {
  constructor(userWindowId, userListId, addContactButtonId, userSearchId) {
    this.USER_PREFIX = "user-";
    this.LIST_ITEM_CLASS = this.USER_PREFIX + "item";
    this.FORMAT_SPAN_CLASS = "fa-li";
    this.FORMAT_I_CLASS = "fas fa-times";
    this.USERS_PER_PAGE = 10;
    this.users = new Set();
    this.userSearchInput = document.getElementById(userSearchId);
    this.userWindow = document.getElementById(userWindowId);
    this.userList = document.getElementById(userListId);
    this.selectedUsers = new Set();
    this.addContactButton = document.getElementById(addContactButtonId);
    this.messageWindowReference = null;
    this.chatWindowReference = null;
    this.userTrie = null;
    this.setUsers();

    this.userSearchInput.addEventListener("input", (function() {
      if (this.userSearchInput.value && this.userSearchInput.value.length > 2) {
        this.users.clear();
        this.searchUsersAjax(this.userSearchInput.value);
      }
      else {
        this.loadUsersAjax(1);
      }
    }).bind(this));

    this.userList.addEventListener("scroll", (function() {
      const scroll = this.userList.scrollHeight 
                     - this.userList.scrollTop
                     - this.userList.clientHeight;
      if (-1 < scroll && scroll < 1) { 
        if (this.userSearchInput.value && this.userSearchInput.value.length > 2) {
          this.searchUsersAjax(this.userSearchInput.value,
                               this.getPageNumber())
        }
        else {
          this.loadUsersAjax(this.getPageNumber(),
                             false);
        }
      }
    }).bind(this));

    this.addContactButton.addEventListener("click", (function () {
      this
      .chatWindowReference
      .addContactsAndChatsAjax(Array.from(this.selectedUsers));
      
      this.selectedUsers.clear();
      for (let listItem of this.userList.children) {
        if (listItem.className.includes(SELECTED_ELEMENT)) {
          listItem.className = listItem
                               .className
                               .replace(" " + SELECTED_ELEMENT, "");
        }
      }

    }).bind(this));

    this.userList.addEventListener("click", (function(event) {
        const item = event.target;
        if (item.tagName.toLowerCase() === "li") {
            const itemClass = item.getAttribute("class");
            const itemId = item.id.split("-")[1];
            if (itemClass.includes(SELECTED_ELEMENT)) {
                this.selectedUsers.delete(itemId);
                item.className = itemClass
                                 .replace(" " + SELECTED_ELEMENT, "");
            }
            else {
                this.selectedUsers.add(itemId);
                item.className =  itemClass + " " + SELECTED_ELEMENT;
            }
        }
        else if (item.tagName.toLowerCase() === "span") {
            const parent = item.parentElement;
            const itemParentClass = parent.getAttribute("class");
            const itemParentId = parent.id.split("-")[1];
            if (itemParentClass.includes(SELECTED_ELEMENT)) {
                this.selectedUsers.delete(itemParentId);
                parent.className = itemParentClass
                                   .replace(" " + SELECTED_ELEMENT, "");
            }
            else {
                this.selectedUsers.add(itemParentId);
                parent.className = itemParentClass + " " + SELECTED_ELEMENT;
            }
        }
        this.updateAddContactButton();
    }).bind(this));    
  }

  addUser(username, userId) {
    if (!this.users.has(userId)) {
        let listItem = document.createElement("li");
        let formatSpan = document.createElement("span");
        let usernameSpan = document.createElement("span");
        let formatI = document.createElement("i");
        listItem.className = this.LIST_ITEM_CLASS;
        listItem.id = this.USER_PREFIX + userId;
        formatSpan.className =  this.FORMAT_SPAN_CLASS;
        formatI.className = this.FORMAT_I_CLASS;
        usernameSpan.innerText = username;
        formatSpan.appendChild(formatI);
        listItem.appendChild(formatSpan);
        listItem.appendChild(usernameSpan);
        this.userList.appendChild(listItem);

        this.users.add(userId);
    }
  };

  addUsers(users, clearArea=true) {
    if (clearArea) {
      this.userList.innerText = "";
      this.users.clear();
      this.selectedUsers.clear();
      this.updateAddContactButton();
    }
    for (let user of users) {
      this.addUser(user["username"], user["user_id"]);
    }
  };

  searchUsersAjax(username, pageNumber=1) {
    let request = new XMLHttpRequest();
    request.open("POST", "/search_users", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    request.onload = (function() {
      try {
        if (request.readyState === request.DONE) {
          if (request.status === 200) {

            const response = JSON.parse(request.response);
            const foundUsers = response["found_users"];
            let clearArea = false;
            if (foundUsers.length > this.users.size || pageNumber < 2) {
              clearArea = true;
            }
            this.addUsers(foundUsers, clearArea);
          }
          else {
            logFailedAjaxRequest(request);
          }
        }
      }
      catch(e) {
        logException(e);
      }
    }).bind(this);

    request.send(JSON.stringify({"username": username,
                                 "page_number": pageNumber}))
  };

  setUsers() {
    for (let listElement of this.userList.children) {
      this.users.add(listElement.id.split("-")[1]);
    }
  }

  getPageNumber() {
    return Math.ceil(this.users.size / this.USERS_PER_PAGE + 1);
  }

  setMessageWindowReference(messageWindowReference) {
    this.messageWindowReference = messageWindowReference;
  }

  setChatWindowReference(chatWindowReference) {
    this.chatWindowReference = chatWindowReference;
  }

  updateAddContactButton() {
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

  loadUsersAjax(pageNumber, clearArea=true) {
    let request = new XMLHttpRequest();
    request.open("POST", "/load_users", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    request.onload = (function() {
      try {
        if (request.readyState === request.DONE) {
          if (request.status === 200) {
            const response = JSON.parse(request.response)
            const addedUsers = response["added_users"];
            if (addedUsers.length > this.users.size) {
              clearArea = true;
            }
            this.addUsers(addedUsers, clearArea);
          }
          else {
            logFailedAjaxRequest(request);
          }
        }
      }
      catch(e) {
        logFailedAjaxRequest(e);
      }

    }).bind(this);

    request.send(JSON.stringify({"page_number": pageNumber}));
  };
};


class ChatWindow {
  constructor(chatWindowId, 
              chatListId,
              removeChatButtonId,
              chatSearchInputId) {
    this.CHAT_PREFIX = "chat-";
    this.LIST_ITEM_CLASS = this.CHAT_PREFIX + "item";
    this.FORMAT_SPAN_CLASS = "fa-li";
    this.FORMAT_I_CLASS = "fas fa-times";
    this.CHATS_PER_PAGE = 10;
    this.chats = new Set();
    this.chatSearchInput = document.getElementById(chatSearchInputId);
    this.chatWindow = document.getElementById(chatWindowId);
    this.chatList = document.getElementById(chatListId);
    this.removeChatButton = document.getElementById(removeChatButtonId);
    this.selectedChatId = null;
    this.messageWindowReference = null;
    this.userWindowReference = null;

    this.setChats();

    this.removeChatButton.addEventListener("click", (function() {
      if (this.selectedChatId) {
          this.removeChatAjax(this
                              .selectedChatId);
      }
    }).bind(this));

    this
    .chatList
    .addEventListener("click", (function(event) {
        if (event.target.tagName.toLowerCase() === "li") {
            const elementId = event.target.id.split("-")[1];
            this.chooseChatAjax(elementId);
        }
        else if (event.target.tagName.toLowerCase() === "span") {
            const elementId = event.target.parentElement.id.split("-")[1];
            this.chooseChatAjax(elementId);
        }
        
    }).bind(this));

    this.chatList.addEventListener("scroll", (function() {
      const scroll = this.chatList.scrollHeight 
                     - this.chatList.scrollTop
                     - this.chatList.clientHeight;
      if (-1 < scroll && scroll < 1) { 
        if (this.chatSearchInput.value && this.chatSearchInput.value.length > 2) {
              this.searchChatsAjax(this.chatSearchInput.value,
                                   this.getPageNumber())
        }
        else {
          this.loadChatsAjax(this.getPageNumber());
        }
      }
    }).bind(this));

    this
    .chatSearchInput.addEventListener("input", (function () {
      if (this.chatSearchInput.value && this.chatSearchInput.value.length > 2) {
        this.chats.clear();
        this.searchChatsAjax(this.chatSearchInput.value);
      }
      else {
        this.loadChatsAjax();
      }
    }).bind(this));
  }

  getPageNumber() {
    return Math.trunc(this.chats.size / this.CHATS_PER_PAGE + 1);
  };

  setChats() {
    for (let chat of this.chatList.children) {
      this.chats.add(chat.id.split("-")[1]);
    }
  };

  searchChatsAjax(chatName, pageNumber=1) {
    let request = new XMLHttpRequest();
    request.open("POST", "/search_chats", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    request.onload = (function() {
      try {
        if (request.readyState === request.DONE) {
          if (request.status === 200) {

            const response = JSON.parse(request.response);
            const foundChats = response["found_chats"];
            let clearArea = false;
            if (pageNumber < 2) {
              clearArea = true;
            }
            this.addChats(foundChats, clearArea);
          }
          else {
            logFailedAjaxRequest(request);
          }
        }
      }
      catch(e) {
        logException(e);
      }
    }).bind(this);

    request.send(JSON.stringify({"chat_name": chatName,
                                 "page_number": pageNumber}))
  };

  chooseChat(currentUsername, chatName, chatId, messages) {
    let lastSelected = null;
    let lastSelectedId = null;
    if (this.selectedChatId) {
      lastSelected = document
                     .getElementById(CHAT_PREFIX + this.selectedChatId);
      lastSelectedId = this.selectedChatId;
    }
    this.selectedChatId = chatId;
    let selectedChat = document.getElementById(CHAT_PREFIX + chatId);
    if (lastSelected) {
      lastSelected.className = lastSelected
                               .className
                               .replace(" " + CURRENT_SELECTED, "");
    }
    
    if (!lastSelected || !(lastSelectedId === chatId)) {
        selectedChat.className = selectedChat
                                 .className + " " + CURRENT_SELECTED;
        this.messageWindowReference.addMessages(currentUsername, messages);
        this.messageWindowReference.setChatHeader(chatName);
        this.messageWindowReference.show();

        this.showRemoveChatButton();
    } else {
        this.hideRemoveChatButton();
        this.messageWindowReference.hide();
        this.selectedChatId = null;
    }

    this.messageWindowReference.scrollDown();
  };

  loadChatsAjax(pageNumber=1, clearArea=false) {
    let request = new XMLHttpRequest();
    request.open("POST", "/load_chats", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);
    request.onload = (function() {
      try {
        if (request.readyState === request.DONE) {
          if (request.status === 200) {
            const response = JSON.parse(request.response)
            const addedChats = response["chats"];
            if (pageNumber < 2) {
              clearArea = true;
            }
            this.addChats(addedChats, clearArea);
          }
          else {
            logFailedAjaxRequest(request);
          }
        }
      }
      catch(e) {
        logFailedAjaxRequest(e);
      }

    }).bind(this);
    request.send(JSON.stringify({"page_number": pageNumber}));
  };

  chooseChatAjax(chatId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/choose_chat", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    request.onload = (function() {
        try {
            if (request.readyState === request.DONE) {
              if (request.status === 200) {
                const response = JSON.parse(request.response);
                const messages = response["messages"];
                const chatName = response["chat_name"];
                const currentUsername = response["current_username"];
                this.chooseChat(currentUsername, chatName, 
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

  addChat(chatName, chatId) {
    if (!this.chats.has(chatId)) {
      let listItem = document.createElement("li");
      let formatSpan = document.createElement("span");
      let chatNameSpan = document.createElement("span");
      let formatI = document.createElement("i");
      listItem.id = this.CHAT_PREFIX + chatId;
      listItem.className = this.LIST_ITEM_CLASS;
      if (chatId == this.selectedChatId) {
        listItem.className += " " + CURRENT_SELECTED;
      }
      formatSpan.className = this.FORMAT_SPAN_CLASS;
      formatI.className =  this.FORMAT_I_CLASS;
      chatNameSpan.innerText = " " + chatName;
      formatSpan.appendChild(formatI);
      listItem.appendChild(formatSpan);
      listItem.appendChild(chatNameSpan);
      this.chatList.appendChild(listItem);
      this.chats.add(chatId);
    }
  };

  addChats(addedChats, clearArea=true) {
    if (clearArea) {
      this.chatList.innerText = "";
      this.chats.clear();
    }
    for (let chat of addedChats) {
      this.addChat(chat["chat_name"],
                   chat["chat_id"]);
    }
    this.userWindowReference.updateAddContactButton();
  };

  addContactsAndChatsAjax(userIds) {
    if (this.userWindowReference.selectedUsers.size) {
      let request = new XMLHttpRequest();
      request.open("POST", "/add_contacts_and_chats", true);
      request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

      request.onload = (function() {
        try {
          if (request.readyState === request.DONE) {
            if (request.status === 200) {
                const response = JSON.parse(request.response);
                const addedChats = response["added_chats"];
                this.addChats(addedChats, false);
            } else {
                logFailedAjaxRequest(request);
            }
          }
        }
        catch(e) {
          logException(e);
        }
      }).bind(this);
      request.send(JSON.stringify({user_ids: userIds}))
    }
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
    if (this.chats.has(chatId)) {
      const listItem = document.getElementById(this.CHAT_PREFIX + chatId);
      this.chatList.removeChild(listItem);
      this.chats.delete(chatId);
      this.selectedChatId = null;
      this.hideRemoveChatButton();
      this.messageWindowReference.hide();
    }
  };

  removeChatAjax(chatId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/remove_chat", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    request.onload = (function() {
      try {
        if (request.readyState === request.DONE) {
          if (request.status === 200) {
            const response = JSON.parse(request.response);
            const chat = response["removed_chat"];
            const chatId = chat["chat_id"];
            this.removeChat(chatId);
          }
          else {
            logFailedAjaxRequest(request);
          }
        }
      }
      catch(e) {
        logException(e);
      }
    }).bind(this);

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
    this.intervalHandle = null;

    this.sendMessageButton.addEventListener("click", (function(){
        if (this.chatWindowReference.selectedChatId) {
          const messageText = this.messageField.value;
          this.sendMessageAjax(this.chatWindowReference.selectedChatId, 
                               messageText);
        }
        else {
          console.log("Can't send the message: no contact selected");
        }
    }).bind(this));
    
  }

  startMessagePolling() {
    if (this.intervalHandle) {
      this.stopMessagePolling();
    }
    this.intervalHandle = window
                          .setInterval(this
                                      .checkNewMessagesAjax
                                      .bind(this),
                                      POLLING_TIMEOUT,
                                      this
                                      .chatWindowReference
                                      .selectedChatId
    );
  };

  stopMessagePolling() {
    clearInterval(this.intervalHandle);
    this.intervalHandle = null;
  };

  setChatHeader(header) {
    this.chatHeader.innerText = header;
  };

  addMessage(currentUsername, message) {
    const text = message["text"];
    const dateCreated = format_date(message["date_created"]);
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
    messageDiv.className = "message";
    
    this.messageArea.appendChild(messageDiv);
    this.messageArea.appendChild(br);
    this.scrollDown();
  };

  addMessages(currentUsername, messages, clearArea = true) {
    if (clearArea) {
      this.messageArea.innerHTML = "";
    }
    for (let message of messages) {
      this.addMessage(currentUsername, message);
    }
  };

  loadMessagesAjax(currentChatId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/load_messages", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    request.onload = (function() {
      try {
          if (request.readyState === request.DONE) {
            if (request.status === 200) {
              const response = JSON.parse(request.response);
              const messages = response["messages"];
              const currentUsername = response["current_username"];
              this.addMessages(currentUsername,
                               messages);
            } else {
              logFailedAjaxRequest(request);
            }
          }
        }
        catch(e) {
          logException(e);
        }
    }).bind(this);

    const data = {
                   chat_id: currentChatId
                 };
    request.send(JSON.stringify(data));
  }

  checkNewMessagesAjax(currentChatId) {
    let request = new XMLHttpRequest();
    request.open("POST", "/check_new_messages", true);
    request.setRequestHeader("Content-Type", JSON_CONTENT_TYPE);

    request.onload = (function() {
      try {
          if (request.readyState === request.DONE) {
            if (request.status === 200) {
              const response = JSON.parse(request.response);
              const messages = response["messages"];
              const currentUsername = response["current_username"];
              this.addMessages(currentUsername,
                                        messages, false);
            } else {
              logFailedAjaxRequest(request);
            }
          }
        }
        catch(e) {
          logException(e);
        }
    }).bind(this);

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

      request.onload = (function(){
          try {
              if (request.readyState === request.DONE) {
                if (request.status === 200) {

                    const response = JSON.parse(request.response);
                    const message = response["message"];
                    const currentUsername = response["current_username"];
                    this.messageField.value = "";
                    this.addMessage(currentUsername, message);
                } else {
                    logFailedAjaxRequest(request);
                }
              }
            }
            catch(e) {
              logException(e);
            }
      }).bind(this);

      const data = {
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

  scrollDown() {
    this.messageArea.scrollTo(0, this.messageArea.scrollHeight);
  };

  show() {
    this.scrollDown();
    this.startMessagePolling();
    this.messageWindow.style.display = "block";
    
    this
    .userWindowReference
    .userWindow
    .className = this.COLUMN_3;
    
    this
    .chatWindowReference
    .chatWindow
    .className = this.COLUMN_3;
  };

  hide() {
    this.stopMessagePolling();
    this.messageField.value = "";
    this.messageWindow.style.display = "none";

    this
    .userWindowReference
    .userWindow
    .className = this.COLUMN_3 + " " + this.CENTER_FROM_LEFT;

    this
    .chatWindowReference
    .chatWindow
    .className = this.COLUMN_3 + " " + this.CENTER_FROM_RIGHT;
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
                                ADD_CONTACT_BUTTON_ID,
                                USER_SEARCH_ID);
let chatWindow = new ChatWindow(CHAT_WINDOW_ID,
                                CHAT_LIST_ID,
                                REMOVE_CHAT_BUTTON_ID,
                                CHAT_SEARCH_INPUT_ID);

messageWindow.setChatWindowReference(chatWindow);
messageWindow.setUserWindowReference(userWindow);
userWindow.setChatWindowReference(chatWindow);
userWindow.setMessageWindowReference(messageWindow);
chatWindow.setUserWindowReference(userWindow);
chatWindow.setMessageWindowReference(messageWindow);

window
.addEventListener("load", function() {
    messageWindow.scrollDown();
    try {
      chatWindow
      .selectedChatId = document
                        .querySelector("." + CURRENT_SELECTED).id.split("-")[1];
    }
    catch(e) {
      console.log('No chat selected');
    }
    if (chatWindow.selectedChatId 
        && chatWindow.chats.has(chatWindow.selectedChatId)) {
        
            chatWindow.showRemoveChatButton();
            messageWindow.loadMessagesAjax(chatWindow.selectedChatId);
            messageWindow.startMessagePolling();
    }
});
