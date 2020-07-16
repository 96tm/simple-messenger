[![License](https://img.shields.io/badge/license-MIT-green)](https://tldrlegal.com/license/mit-license)
<br>

# Simple Messenger
A client-server messenger built with Flask.<br>
It uses WebSocket API<br> 
(flask-socketio for the server, socket.io for the client, gevent as a transport)<br> 
and features a tiny REST API.<br>
PostgreSQL or sqlite3 can be used as RDBMS.

<details>
  
 <summary> 
    Database schema
  </summary>
  
  <br>
  
  ![Database schema](./screenshots/schema.png)
  <i>Made using <a href="https://pgmodeler.io/">pgmaker</a></i> 

</details>

<details>

  <summary>
      Screenshots
  </summary>
    
  <br>
    
  ![Registration page](./screenshots/2.png)
  <i>Registration page</i>
  
<br>

  ![After registration](./screenshots/3.png)
  <i>After registration, the user is automatically logged in, but stays unconfirmed - they have to check the inbox and follow the provided link </i> 
  
<br>

  ![Confirmation is completed](./screenshots/4.png)
  <i>Confirmation is completed</i>
  
<br>

  ![Logged out](./screenshots/5.png)
  <i>Logged out</i>
  
<br>

  ![Wrong user data](./screenshots/6.png)
  <i>Wrong user data</i>
  
<br>

  ![Main page](./screenshots/7.png)
  <i>Main page</i>
  
<br>

  ![Main page, several users selected](./screenshots/8.png)
  <i>Main page, several users selected</i>
  
<br>

  ![Main page, 3 unread messages](./screenshots/9.png)
  <i>Main page, 3 unread messages</i>
  
<br>

  ![Main page, chat selected](./screenshots/10.png)
  <i>Main page, chat selected</i>
  
<br>

  ![Main page, users and chats are filtered](./screenshots/11.png)
  <i>Main page, users and chats are filtered</i>
  
<br>

  ![Main page, users and chats filtered, no chats found](./screenshots/12.png)
  <i>Main page, users and chats filtered, no chats found</i>
  
<br>

  ![Generic error page](./screenshots/404.png)
  <i>Generic error page</i>   
    
</details>

<details>
  
  <summary>
    Installation
  </summary>
  
  <br>

  The easiest way to run the app is to create a Docker image and then run a container.<br>
  If you have a Debian based system (Ubuntu, Mint...), the following steps should work:<br>
  - clone the repository
  ```
  $ git clone https://github.com/96tm/simple-messenger.git
  ```
  - navigate to the project directory (Dockerfile is inside) and create a Docker image
  ```
  $ sudo docker build -t simple_messenger:latest .
  ```
  - download a Postgres image
  ```
  $ sudo docker pull postgres
  ```
  - run a Postgres container replacing "/directory/to/mount" with an appropriate directory
    to store the database <br>
    (if you have Postgres service on your system, 
    you'll need to stop it with  something like <br>
    ```$ sudo service postgresql stop```)
  ```
  $ sudo docker run --name postgres -d -p 5432:5432 \
    -e POSTGRES_USER=postgres_user \
    -e POSTGRES_PASSWORD=postgres_password \
    -e POSTGRES_DB=db_name \
    -v /directory/to/mount:/var/lib/postgresql/data \
    --rm postgres:latest
  ```
  - run a container with the Simple Messenger image<br>
    (you'll need to assign appropriate values to<br>
     ```SECRET_KEY```, ```MAIL_SERVER```, ```MAIL_SENDER```,
     ```MAIL_USERNAME``` and ```MAIL_PASSWORD```;<br>
     also, if you don't want to add fake users for testing,
     remove the line <br>
     ```-e ADD_TEST_USERS=1 \```)
  ```
  $ sudo docker run --name simple_messenger -d -p 8000:5000 \
    -e ADD_TEST_USERS=1 \
    -e SECRET_KEY=make_it_secret \
    -e SESSION_TYPE=filesystem \
    -e MAIL_SERVER=mail_server \
    -e MAIL_SENDER=mail@send.er \
    -e MAIL_PORT=587 \
    -e MAIL_USE_TLS=true \
    -e MAIL_USERNAME=username \
    -e MAIL_PASSWORD="password" \
    --link postgres:dbserver \
    -e DATABASE_URI=postgresql://postgres_user:postgres_password@dbserver/db_name \
    --rm simple_messenger:latest
  ```
  Now you can open the app at <a href="http://localhost:8000">localhost:8000 </a> and register.<br>
  If test users were added (```-e ADD_TEST_USERS=1```),<br>
  you can log in right away 
  with the following email/password pairs:
  - email: ```arthur@arthur.arthur```, password: ```arthur```;
  - email: ```morgain@morgain.morgain```, password: ```morgain```;
  - email: ```merlin@merlin.merlin```, password: ```merlin```.
</details>

<details>
  
 <summary> 
  REST API
 </summary>
 
 The following actions are available:
 - get a list of the authenticated user's chats
 ```/api/v1.0/chats```;
 - get a chat by id
 ```/api/v1.0/chats/1```;
 - get a list of messages in the chat
 ```/api/v1.0/chats/1/messages```;
 - get a message by the id from the chat
 ```/api/v1.0/chats/1/messages/1```;
 - send a message
 ```/api/v1.0/chats/1/messages/```.

 Sending a message requires a JSON object in the form 
 ```{"text" :"your_message_text"}```
 in the request.
 
</details>
