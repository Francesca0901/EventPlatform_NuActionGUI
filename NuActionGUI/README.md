# README

This is a dockerized version of the ActionGUI framework. To start make sure you have docker installed and type:

`docker compose up`

to build the images and run the containers the first time you use them. 

Once the images have been built you can start and stop the containers using:

`docker-compose up`

and

`docker-compose stop`

## Compiling the project

Once the containers are running (you can check this with `docker ps`  and you should see a 
mysql5 container and a container named `nag-app`) you can open a shell inside the 
maven container using:

`docker exec -it nag-app bash`

The directory `/app` in the container is linked to the
local `/NuActionGUI` folder. Anything you create in this folder 
will be visible on your host machine (and vice-versa).

The `/app/project` directory contains the EventPlatformNAG application implemented naively: there are no privacy policy as well as all actions are allowed (i.e., fullAccess) for all roles (Note that some of the functionality may break since `VISITOR` user is not an actual user).

Your task is to define the security and privacy model in `/app/models/EventPlatformNAG` according to the provided project description.

## Regenerate the security and privacy parts of the project

Navigate to the `/app/src` directory and build the virtual environment and install necessary packages inside this environment:

```
python3 -m venv .venv
. .venv/bin/activate
(.venv) $ pip3 install -r requirements.txt
```

Then, to recompile and generate security and privacy parts of the project again:

`python3 generate.py -p EventPlatformNAG -o project -re`

Note that, you may have to remove the current instance of the database (it is located in `/app/project/EventPlatformNAG/instance/`).

## Running the project

Finally, to execute the compiled web application, go to the `/app/project/EventPlatformNAG` directory (inside the virtual environment):

`flask --app app.py run --host=0.0.0.0`

The app should be reachable from your local machine under `localhost:5000`

## More information
Refer to the NuActionGUI tutorials for more information.

## Testing the project
To be announced
