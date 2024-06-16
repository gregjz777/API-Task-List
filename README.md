# API To-Do-List
Simple application written in Python to manage a list of to-do tasks for different users. Each user, after registering, has the ability to create his/her own list of tasks, display tasks as a schedule for a given day/week/month or display all the tasks simultaneously in the form of a list. Each of the added tasks can also be edited, mark/unmark as completed or deleted. 

## Used technologies
- Python 3.9
- Flask
- Marshmallow
- SQLAlchemy
- Werkzeug
- Swagger

## Installation
### Dependencies
To install all necessary packages,navigate to the directory containing project in your terminal and run the following command :
````
pip install -r requirements.txt
````

### Database configuration
It is necessary to modify line number 26 by specifying an appropriate URI that will point to the existing database. When you run the application for the first time, it will itself create the tables necessary for its operation based on the models defined in the code.

#### For MySQL:
````
mysql://username:password@host:port/database_name
````

#### For PostgreSQL:"
````
postgresql://username:password@host:port/database_name
````

#### Example:
````
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://baza:SwF7Qn:WLc+98L]@192.168.75.159:3306/baza_danych_projekt"
````



## Quick start and usage
Once launched, the application is ready to accept requests via the https protocol, for example, using the program "postman"
![image](readme/postman.png)

### Available methods
- `"GET /uzytkownik/logowanie"` : Method that verifies credentials and returns an access token; authentication is done via HTTP basic authentication form.
- `"POST /uzytkownik"` : Creates a new user.
- `"POST /uzytkownik/admin"` : Creates a new user with admin privileges - required admin privileges for current user
- `"GET  /uzytkownik"` : Downloads all users - administrator rights required
- `"DELETE /uzytkownik/{id_wybranego_uzytkownika}"` : Deletes a user with the specified id number - administrator privileges required
- `"POST /zadanie"` : Add a new task to the task list
- `"PUT /zadanie/{id_wybranego_zadania}"` : Update an existing task with the indicated id in the task list.
- `"DELETE /zadanie/{id_wybranego_zadania}"` : Deletes the task
- `"GET /zadanie/{id_wybranego_zadania}"` : Downloads one task with the indicated id
- `"GET /zadanie/wszystkie"` : Downloads all tasks of a given user
- `"POST /zadanie/filtr"` : Downloads the task schedule for a given day, week or month
- `"PUT /zadanie/wykonaj/{id_wybranego_zadania}"` : When called, the method marks a non-executed task as executed, while when called on an executed task, it unmarks it (the task becomes non-executed again)

### Swagger
For testing purposes, interactive documentation is available after the application is launched, thanks to the Swagger toolkit. Just type in the address of your web browser:
````
https://127.0.0.1:5000/api/docs/
````
![image](readme/swagger.png)

Click on the green button located in the upper right corner of the screen called "Authorize"
![image](readme/swagger1.png)

Enter the user data that you defined earlier in the database:
![image](readme/swagger2.png)

Then click on the available GET method "/uzytkownik/logowanie", "Try it out" and "Execute". In response, you should receive a JWT Token, necessary for executing the rest of the available queries.
![image](readme/swagger3.png)
![image](readme/swagger4.png)

## Important features
### Authentication
All methods (except "token check", "create new user" and "login") require the user to log in using existing credentials in the database

### JSON Web Token
When a user logs in, a JWT (JSON Web Token) is sent to the user, which is required to execute all methods except the three mentioned above; it contains information about the user's public id and the date with a time offset of 30 minutes from its creation.
- The public id "covers up" the real id of the user in the database, which can make a potential attack much more difficult; based on it, the user in the database is found
- The time limitation imposes the need to log in again after 30 minutes, making it impossible to use the same token indefinitely

### Authorization
There are 3 methods available for user type "admin": "delete user", "add admin" and "display all users". These methods, in addition to logging in, require the user to have a value of 1 (True) in the admin column of the database, which is checked before calling the actual part of the method (this value can only be given by another admin when adding a new user with admin privileges, or by direct modification of the entry by an authorized user in the database)

### JSON input body validation
For each input coming from the user, schemas have been created with the help of classes, which are called before the data is used by the backend in a particular method in order to verify its correctness (comparing the range in the case of numbers, length in the case of strings, storage format in the case of date and time, and specific values in the case of a predefined range used when filtering a list of tasks).

### SQLAlchemy
The backend does not contain directly written "raw" SQL commands. They are implemented with the help of the SQLAlchemy library, which is an object-relational mapper that allows data structures to be represented in object-oriented form. Built-in security mechanisms here protect against SQL Injection attacks and provide support for a transaction mechanism responsible for data consistency and integrity in case of errors or failures;

### CORS
CORS (Cross-Origin Resource Sharing) only allows connection from 3 domains (port 5000 for queries for the backend and for documentation in the swager, port 5173 for the frontend). All other queries will be automatically rejected.
![image](readme/cors.png)

### TLS
The exchange of information between the frontend and the backend is carried out using a TLS-encrypted connection, which is made possible by using a self-signed certificate generated with OpenSSL. In the case of a production environment, it would be necessary to replace such a certificate with a "real" one, such as one generated using the free "Let's Encrypt" service)