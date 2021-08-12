## About

This is a replacement to the Jama Connect dashboards for projects and test plans, with support for the automatic generation of charts and figures from each test plan's data.

### Built With

* [Python](https://www.python.org/downloads/source/)
* [Plotly](https://plotly.com/)
* [Redis](https://redis.io/topics/quickstart)
* [Celery](https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html)

## Deployment

To deploy the Plotly dashboard, follow these steps.

### Prerequisites

To deploy this tool, you will need a linux OS to manage the Redis database. The dashboard can still be hosted on a Windows machine, but Redis must be handled by linux. Make sure Python (preferably 3.6 or greater, but older versions may work) is installed on your system, along with pip. Also install and start Redis if it isn't already running. Once all of those are installed, install the required packages with pip:
```sh
pip install -r requirements.txt
```

Using an older version of Python may cause some of the packages to fail installing. If that happens, try installing the package without the version specified and the tool should still work, though no gurantees are made.

### Configuration

The dashboard is set up to track the Velocity Releases project (VRel), which has the project ID 268. To change the projects the dashboard pulls data from, navigate to the "projects" field of jama-report-config.json and add/remove the appropriate project IDs from the array. Make sure to git pull the changes to the server if not changing the file directly on the server. To get the ID of a project, navigate to one of the project's pages on Contour and copy the number in the link.

![project-id.png](/images/project_id.png)
![config.png](/images/config.png)

### Updating Data

Pulling the data from Contour requires some variables to be set up properly. **It is recommended to do the following in a screen or tmux window to keep the processes alive after disconnecting from SSH.** Set these environment variables, replacing the values with appropriate alternatives as needed. 
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

To update the data periodically using Celery, run these commands. The Celery task is configured to update the data every 30 minutes.

```sh
celery -A tasks beat --loglevel=INFO &
celery -A tasks worker --loglevel=INFO &
```

Once the commands have been run, feel free to detach from the screen/tmux window (Ctrl-A then press D for screen). The data will continue to be updated in the background. To return to the screen window, type the following, replacing ID with the session ID of the screen:

```sh
screen -ls      # list the IDs of the running screens
screen -r ID    # return to a screen
```

### Serving the Dashboard

**In a new screen or tmux window**, set the REDIS_URL environment variable like before:

```sh
export REDIS_URL='redis://localhost:6379/0'
```
Then start the Dash server using this command:
```sh
python3 server.py
```

At this point the dashboard can be accessed at IP:8080, where IP is the IP address of the machine the server command was run on. Again, feel free to detach from the screen/tmux and disconnect from SSH.

## Usage

### Dropdowns

The dashboard is based around various dropdowns that filter the data. The main dropdowns at the top allow you to select the test plan, test cycle, test group, and priority of the test runs, and will update all of the charts when any of them are changed.

![main-dropdown.png](/images/main_dropdown.png)

Where it is applicable, charts will have a dropdown to filter by week. This will only update the chart associated with the dropdown. In addition, all charts can be hidden with their respective collapse buttons.

![week-dropdown.png](/images/week_dropdown.png)

### Line Chart

The historical status line chart allows you to observe the status of all the test runs over time. Choosing a start date will start the graph at that date; otherwise, the graph starts at creation date of the oldest test run. Choosing a test deadline will generate a required test run rate dotted line that shows the rate at which the remaining test runs need to be executed in order for all runs to finish before that date. The two check boxes will have the chart treat blocked or in progress runs as not run if checked.

![line-chart.png](/images/line_chart.png)

### Bar Charts

Each bar chart has a checklist that will modify which statuses appear in the chart. By default, all of the statuses are checked. You can zoom in by using a click-and-drag gesture, selecting which parts of the chart to zoom in on. Zoom back out by double clicking the chart.

![bar-chart.png](/images/bar_chart.png)

### Test Runs Table

The columns shown in the test runs table can be configured using the 'Toggle Columns' button, where the desired columns can be selected or deselected. The table can be filtered by typing a search string into the field below the header of each column (case-sensitive). The 'Export' button will save the data with all filters applied to a csv file.

![table.png](/images/table.png)

## Full App Showcase

![full_app.png](/images/full_app.png)