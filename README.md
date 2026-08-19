# MetsIS - Workdesk for forest buyers.

## Prerequisites for development

* JDK 13+
* NodeJS v13.12.0+
* NPM 6.14.4+
* Docker version 19.03.8, build afacb8b +
* docker-compose version 1.25.4, build 8d51620a +

### Setting up development database

MetsIS uses PostgreSQL as its database. This repository contains a Dockerfile with minimum viable configuration to get a running database in development.
To build this to a usable image, run the following command: `cd $PROJECT_ROOT/dockerfiles/postgres-dev && sh build.sh`

Now you have an empty Postgres Database image with correct roles and privileges preset.

To start the database run in `$PROJECT_ROOT`: `docker-compose up -d`

To check the status of the database run: `docker ps`. If there is a line with string `metsis-postgres:latest`, then all should be OK. If not, consider running docker-compose again.

### Setting up backend

To build the backend run in `$PROJECT_ROOT`: `./gradlew clean build`

To run the backend through you IDE:
 
1. Locate the class AppRunner and run it. 
2. It will fail and complain you need to feed the properties file to it.
3. In IntelliJ, open in project tree: `metsis-ee-api/src/test/resources`.
4. Right click on the file `test-full-conf.properties` and from the dropdown, select `Copy Path`.
5. In upper right corner, left from the play button, click on the selectbox with `AppRunner` in it.
6. In the dropdown click `Edit Configurations...`
7. Paste what you copied to `Program arguments` input. It should be the full path to `test-full-conf.properties`.
8. Save the changes and run the application again.

By now, backend should have started up.

### Setting up frontend

1. In command line, move to folder `metsis-ee-client`
2. Run `npm install`
3. Run `npm run:start`

UI should be running by now.

### Now what?

Assuming you completed all previous steps successfully, you should have a running application on http://localhost:4200.

There should also be one user in it with username `autocreated` and password `autocreated`.
Use it to log in and create new users, modify user privileges and so on. 
Keep in mind that `autocreated` user itself initially only has admin privileges which means he can only see admin stuff (not forestry related stuff).

**NB!** Initially there are absolutely no owners or cadastres in the database. You either have to insert them manually or import some kind of from some live environment. 
To manually insert an owner, make sure you have `OWNERS` privilege and move to URL `http://localhost:8080/owners/owners-ssn-or-reg-code-you-would-like-to-add`. 
There you can add the owner to database.

Happy developing!
