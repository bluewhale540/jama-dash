## About

This is a replacement to the Jama Connect dashboards for projects and test plans, with support for the automatic generation of charts and figures from each test plan's data.

### Screenshots


### Built With

* [Python](https://www.python.org/downloads/source/)
* [Plotly](https://plotly.com/)
* [Redis](https://redis.io/topics/quickstart)
* [Celery](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html)

## Deployment

To deploy the Plotly dashboard, follow these steps.

### Prerequisites

To deploy this tool, you will need a linux OS to manage the Redis database. The dashboard can still be hosted on a Windows machine, but Redis must be handled by linux. Make sure Python (preferably 3.6 or greater, but older versions may work) is installed on your system, along with pip. Also install Redis if it isn't already. Once all of those are installed, install the required packages with pip:
```sh
pip install -r requirements.txt
```

Using an older version of Python may cause some of the packages to fail installing. If that happens, try installing the package without the version specified and the tool should still work, though no gurantees are made.

### Configuration

The dashboard is set up to track the Velocity Releases project (VRel), which has the project ID 268. To change the projects the dashboard pulls data from, navigate to the "projects" field of jama-report-config.json and add/remove the appropriate project IDs from the array. To get the ID of a project, navigate to one of the project's pages on Contour and copy the number in the link.

![project-id.png](https://i.postimg.cc/9FzBjF7d/project-id.png)

### Updating Data

Pulling the data from Contour requires some variables to be set up properly. It is recommended to do the following in a screen or tmux window to keep the processes alive after disconnecting from SSH. Set these environment variables, replacing the values with appropriate alternatives as needed. 
```sh
export REDIS_URL='redis://localhost:6379/0'
export JAMA_API_URL='https://paperclip.idirect.net'
export JAMA_API_USERNAME='*******'
export JAMA_API_PASSWORD='*******'
```
To update the data manually, run update.py:
```sh
python3 update.py
```
To update the data periodically using Celery, run these commands:
```sh
celery -A tasks beat --loglevel=INFO &
celery -A tasks worker --loglevel=INFO &
```

### Serving the Dashboard

In a new screen or tmux window, 