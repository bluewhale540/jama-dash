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

To deploy this tool, you will need a linux OS to manage the Redis database. The dashboard can still be hosted on a Windows machine, but Redis must be handled by linux. Make sure Python (preferably 3.9 or greater, but older versions may work) is installed on your system, along with pip. Also install Redis and Celery (optional, ignore if updating data manually or using a different automation tool), if they are not. 

### Configuration

The dashboard is set up to track the Velocity Releases project (VRel), which has the project ID 268. To change the projects the dashboard pulls data from, navigate to the "projects" field of jama-report-config.json and add/remove the appropriate project IDs from the array. To get the ID of a project, navigate to one of the project's pages on Contour and copy the number in the link.

![project-id.png](https://i.postimg.cc/9FzBjF7d/project-id.png)

### Execution

Getting the dashboard running requires the environment to be set up properly. Set the following environment variables, replacing the values with appropriate alternatives if needed.
```sh
export REDIS_URL='redis://localhost:6379/0'
export JAMA_API_URL='https://paperclip.idirect.net'
export JAMA_API_USERNAME='*******'
export JAMA_API_PASSWORD='*******'
```