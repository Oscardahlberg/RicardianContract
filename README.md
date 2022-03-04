# RicardianContract
Made for the course D0020E at LTU

This project connects the node database neo4j through a Policy Machine system
with a negotiation engine(https://github.com/EricChiquitoG/NegotiationEngine) to create a frontend for sharing data.

<h2>Getting started.</h2>

<h3>Docker</h3>
First of all we need to launch some kind of server with the policy machine. For this purpouse we have used Docker together with a tomcat server and neo4j.
For instructions on setting up the Docker we reffer to the Policy Machine github: https://github.com/PM-Master/Policy-Machine.

<h3>MongoDB</h3>
We also need to have a server for handeling datasets, contracts and login information. Here we use MongoDB hosted on https://cloud.mongodb.com/. For instructions on how to setup the MongoDB we reffer to https://docs.mongodb.com/manual/installation/.

<h3>Required Libraries</h3>
Flask </br>
werkzeug </br>
flask_bootstrap </br>
pymongo </br>
json </br>
...

<h2>Running the program</h2>
Now you should have all the components required to run the program. But before you run app.py you have to change your mongoDB url so that the program can access your mongoDB, you can do this in db.py. When you run the program for the first time you also have to generate a session for the NGAC. You can do this by uncommenting the "ngac.sessions()" line in app.py then take the ouput and put it in the session var in ngac.py

<h2>How it works</h2>
The program is split up in to two systems. The first one is the NGAC rest api that is running on our docker setup. This allows us to make POST/GET calls then modifies the NGAC graph or returns associations/assignments. The second part of the program is the python/flask system. This is where we make all the restAPI calls aswell as handle everything thats happening on the frontend.
