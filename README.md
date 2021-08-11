## About

This is a replacement to the Jama connect dashboards for projects and test plans, with support for the automatic generation of charts and figures from each test plan's data.

### Built With

* [Python](https://www.python.org/downloads/source/)
* [Plotly](https://plotly.com/)
* [Redis](https://redis.io/topics/quickstart)
* [Celery](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html)

## Deployment

To deploy the Plotly dashboard, follow these steps.

### Prerequisites

To deploy this tool, you will need a linux OS to manage the Redis database. 
Make sure Python (preferably 3.9 or greater, but older versions may work) is installed on your system, along with pip. Also install Redis and Celery, if they are not. 
