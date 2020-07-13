"use strict";


// server sends numbers as strings on requests
// assume moment.js is loaded
// assume socket.io is loaded


// constants

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
const CHAT_UPDATED = "updated-chat";
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
    this.LIST_ITEM_CLASS = "list-group-item";
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
        this.searchUsers(this.userSearchInput.value);
      }
      else {
        this.loadUsers(1);
      }
    }).bind(this));

    this.userList.addEventListener("scroll", (function() {
      const scroll = this.userList.scrollHeight 
                     - this.userList.scrollTop
                     - this.userList.clientHeight;
      if (-1 < scroll && scroll < 1) { 
        if (this.userSearchInput.value && this.userSearchInput.value.length > 2) {
          this.searchUsers(this.userSearchInput.value,
                           this.getPageNumber())
        }
        else {
          this.loadUsers(this.getPageNumber(),
                         false);
        }
      }
    }).bind(this));

    this.addContactButton.addEventListener("click", (function () {
      this
      .chatWindowReference
      .addContactsAndChats(Array.from(this.selectedUsers));
      
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
        let usernameSpan = document.createElement("span");
        listItem.className = this.LIST_ITEM_CLASS;
        listItem.id = this.USER_PREFIX + userId;
        usernameSpan.innerText = username;
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

  searchUsers(username, pageNumber=1) {
    console.log('searching users ' + username)
    SOCKET.emit("search_users",
                {"username": username,
                 "page_number": pageNumber})
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

  loadUsers(pageNumber, clearArea=true) {
    SOCKET.emit("load_users",
                {"page_number": pageNumber,
                 "clear_area": clearArea});
  };
};


class ChatWindow {
  constructor(chatWindowId, 
              chatListId,
              removeChatButtonId,
              chatSearchInputId) {
    this.CHAT_PREFIX = "chat-";
    this.LIST_ITEM_CLASS = "list-group-item";
    this.CHATS_PER_PAGE = 10;
    this.MESSAGES_COUNT_SPAN_CLASS = "badge badge-primary\
                                      badge-pill list-group-item-dark";
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
        SOCKET.emit("remove_chat", {chat_id: this.selectedChatId});
      }
    }).bind(this));

    this
    .chatList
    .addEventListener("click", (function(event) {
        if (event.target.tagName.toLowerCase() === "li") {
            const elementId = event.target.id.split("-")[1];
            this.chooseChat(elementId);
        }
        else if (event.target.tagName.toLowerCase() === "span") {
            const elementId = event.target.parentElement.id.split("-")[1];
            this.chooseChat(elementId);
        }
        
    }).bind(this));

    this.chatList.addEventListener("scroll", (function() {
      const scroll = this.chatList.scrollHeight 
                     - this.chatList.scrollTop
                     - this.chatList.clientHeight;
      if (-1 < scroll && scroll < 1) { 
        if (this.chatSearchInput.value && this.chatSearchInput.value.length > 2) {
              this.searchChats(this.chatSearchInput.value,
                               this.getPageNumber())
        }
        else {
          this.loadChats(this.getPageNumber());
        }
      }
    }).bind(this));

    this
    .chatSearchInput.addEventListener("input", (function () {
      if (this.chatSearchInput.value && this.chatSearchInput.value.length > 2) {
        this.chats.clear();
        this.searchChats(this.chatSearchInput.value);
      }
      else {
        this.loadChats();
      }
    }).bind(this));
  }

  setChatAsUpdated(chatId, unreadMessagesCount) {
    let chatItem = document.getElementById(CHAT_PREFIX + chatId);
    let chatNameSpan = document.querySelector("#" + chatItem.id + " span");
    let messagesCountSpan = chatNameSpan.nextElementSibling;
    if (messagesCountSpan) {
      messagesCountSpan.innerText = unreadMessagesCount;
    }
    else {
      let span = document.createElement("span");
      span.className = this.MESSAGES_COUNT_SPAN_CLASS;
      span.innerText = unreadMessagesCount;
      chatItem.appendChild(span);
    }
  };

  unsetChatAsUpdated(chatId) {
    let chatItem = document.getElementById(CHAT_PREFIX + chatId);
    let chatNameSpan = document.querySelector("#" + chatItem.id + " span");
    let messagesCountSpan = chatNameSpan.nextElementSibling;
    console.log('first' + chatNameSpan);
    console.log('second' + messagesCountSpan);
    if (messagesCountSpan) {
      chatItem.removeChild(messagesCountSpan);
    }
  };

  getPageNumber() {
    return Math.trunc(this.chats.size / this.CHATS_PER_PAGE + 1);
  };

  setChats() {
    if (this.chatList) {
      for (let chat of this.chatList.children) {
        this.chats.add(chat.id.split("-")[1]);
      }
    }
  };

  searchChats(chatName, pageNumber=1) {
    SOCKET.emit("search_chats",
                {"chat_name": chatName,
                 "page_number":pageNumber});
  };


  chooseChatItem(currentUsername, chatName, chatId, messages) {
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
        selectedChat.className = selectedChat.className 
                                 + " " 
                                 + CURRENT_SELECTED;
        this.messageWindowReference.addMessages(currentUsername, messages);
        this.messageWindowReference.setChatHeader(chatName);
        this.messageWindowReference.show();
        this.unsetChatAsUpdated(chatId);
        this.showRemoveChatButton();
    } else {
        this.hideRemoveChatButton();
        this.messageWindowReference.hide();
        this.selectedChatId = null;
    }

    this.messageWindowReference.scrollDown();
  };
  
  loadChats(pageNumber=1) {
    SOCKET.emit("load_chats", {page_number: pageNumber});
  };

  chooseChat(chatId) {
    SOCKET.emit("choose_chat", {chat_id: chatId});
  };

  addChat(chatName, chatId) {
    if (!this.chats.has(chatId)) {
      let listItem = document.createElement("li");
      let chatNameSpan = document.createElement("span");
      listItem.id = this.CHAT_PREFIX + chatId;
      listItem.className = this.LIST_ITEM_CLASS;
      if (chatId == this.selectedChatId) {
        listItem.className += " " + CURRENT_SELECTED;
      }
      chatNameSpan.innerText = " " + chatName;
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


  addContactsAndChats(userIds) {
    if (this.userWindowReference.selectedUsers.size) {
      SOCKET.emit("add_contacts_and_chats", 
                  {user_ids: userIds});
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

    this.sendMessageButton.addEventListener("click", (function(){
        if (this.chatWindowReference.selectedChatId) {
          const messageText = this.messageField.value;
          this.sendMessage(this.chatWindowReference.selectedChatId, 
                           messageText);
        }
        else {
          console.log("Can't send the message: no contact selected");
        }
    }).bind(this));
    
  }

  loadMessages(chatId) {
    SOCKET.emit("load_messages",
                {"chat_id": chatId})
  };


  setChatHeader(header) {
    this.chatHeader.innerText = header;
  };

  addMessage(currentUsername, message) {
    const text = message["text"];
    const dateCreated = format_date(message["date_created"]);
    const sender_username = message["sender_username"];
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

  sendMessage(chatId, messageText) {
    const text = messageText.trim();
    if (text) {
      SOCKET.emit("send_message", {chat_id: chatId, message_text: text});
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


let SOCKET = io.connect('http://' + document.domain + ':' + location.port);


window
.addEventListener("load", function() {
    SOCKET.on("load_messages", function(response) {
      const messages = response["messages"];
      const currentUsername = response["current_username"];
      messageWindow.addMessages(currentUsername,
                                messages);
    });
    SOCKET.on("search_users", function(response) {
      const foundUsers = response["found_users"];
      const pageNumber = response["page_number"];
      let clearArea = false;
      if (foundUsers.length > userWindow.users.size || pageNumber < 2) {
        clearArea = true;
      }
      userWindow.addUsers(foundUsers, clearArea);
    });
    SOCKET.on("load_users", function(response) {
      const addedUsers = response["added_users"];
      let clearArea = response["clear_area"];
      if (addedUsers.length > userWindow.users.size) {
        clearArea = true;
      }
      userWindow.addUsers(addedUsers, clearArea);
    });
    SOCKET.on("search_chats", function(response) {
      const foundChats = response["found_chats"];
      const pageNumber = response["page_number"];
      let clearArea = false;
      if (pageNumber < 2) {
        clearArea = true;
      }
      chatWindow.addChats(foundChats, clearArea);
    });
    SOCKET.on("load_chats", function(response) {
      let clearArea = false;
      const addedChats = response["chats"];
      const pageNumber = response["page_number"];
      if (pageNumber < 2) {
        clearArea = true;
      }
      chatWindow.addChats(addedChats, clearArea);
    });
    SOCKET.on("chat_updated", (function(message) {
      console.log('updated')
      const chats = message["chats"];
      for (let chat of chats) {
        const chatId = chat["chat_id"];
        const unreadMessagesCount = chat["unread_messages_count"];
        const chatName = chat["chat_name"];
        if (!chatWindow.chats.has(chatId)) {
          chatWindow.addChat(chatName, chatId);
        }
        if (chatWindow.selectedChatId === chatId) {
          messageWindow.addMessages(message["current_username"],
                                    message["current_chat_messages"],
                                    false);
          SOCKET.emit("flush_messages", {chat_id: chatId});
        }
        else {
          console.log('updating' + unreadMessagesCount);
          chatWindow.setChatAsUpdated(chatId, unreadMessagesCount);
        }
      }
    }));

    SOCKET.on("remove_chat", function(data) {
      const chatId = data["chat_id"];
      chatWindow.removeChat(chatId);
    });
    
    SOCKET.on("add_contacts_and_chats", function(data) {
      console.log('add contacts and chats')
      const addedChats = data["added_chats"];
      chatWindow.addChats(addedChats, false);
    });

    SOCKET.on("choose_chat", function(data) {
      console.log('choosing');
      const messages = data["messages"];
      const chatName = data["chat_name"];
      const currentUsername = data["current_username"];
      const chatId = data["chat_id"];
      chatWindow.chooseChatItem(currentUsername, chatName, 
                                chatId, messages);
    });

    SOCKET.on("send_message", function(data) {
      const message = data["message"];
      const currentUsername = data["current_username"];
      messageWindow.messageField.value = "";
      messageWindow.addMessage(currentUsername, message);
    });

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
            messageWindow.loadMessages(chatWindow.selectedChatId);
    }
});
