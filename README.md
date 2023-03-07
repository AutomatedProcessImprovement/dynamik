# What is `expert`?

```expert``` stands for ***explainable performance drift***, an algorithm for detecting changes in the cycle time of a
process execution and, if present, to provide insights about the actionable causes of the change.

You can find more details about the algorithm in the following article:

<div style="background-color: #EFEFEF; display: flex; flex-direction: column; padding: 1em; position: relative;">
    <p style="
        font-weight: 700;
        font-size: 1.2em;
        margin: 0;
    ">
        Article title
    </p>
    <p style="
        font-style: italic;
        font-size: .85em;
        font-weight: 500;
        color: #A0A0A0;
        margin: 0;
    ">
        Authors
    </p>
    <p style="
        margin: 0;
        font-size: .85em;
        font-weight: 400;
        color: #A0A0A0;
    ">
        Publisher
    </p>
</div>

# Quickstart

`expert` is designed to be executed using an event log as it's input, processing it sequentially, event by event,
mimicking
an online environment where events are consumed from an event stream.

## Running `expert` from the CLI

To run the algorithm in your command line, you need an event log in CSV or JSON format.

If in CSV, the file is expected to have a headers row which is followed by a row per event:

```csv
case,                   start,                     end,   activity,        resource
2182, 2023-02-24T05:28:00.843, 2023-02-24T05:28:00.843,      START, resource-000001
2182, 2023-02-24T05:28:00.843, 2023-02-24T05:34:31.219, Activity 1, resource-000044
2182, 2023-02-24T05:34:31.219, 2023-02-24T05:47:25.817, Activity 2, resource-000024
2182, 2023-02-24T05:47:25.817, 2023-02-24T05:59:46.195, Activity 3, resource-000010
2182, 2023-02-24T05:59:46.193, 2023-02-24T05:59:46.193,        END, resource-000001
7897, 2023-03-01T08:39:42.861, 2023-03-01T08:39:42.861,      START, resource-000001
7897, 2023-03-01T08:39:42.861, 2023-03-01T08:53:41.167, Activity 1, resource-000029
7897, 2023-03-01T08:53:41.167, 2023-03-01T08:56:46.299, Activity 2, resource-000007
7897, 2023-03-01T08:56:46.299, 2023-03-01T09:12:49.468, Activity 3, resource-000018
7897, 2023-03-01T09:12:49.468, 2023-03-01T09:12:49.468,        END, resource-000001
 ...                      ...                      ...         ...             ...
```

In the case of a JSON file, an array of objects is expected, where each object contains an event:

```json
[
    {
        "case": "2182", "activity": "Activity 3", "resource": "resource-000001",
        "start": "2023-02-24T05:28:00.843", "end": "2023-02-24T05:28:00.843"
    },
    {
        "case": "2182", "activity": "Activity 1", "resource": "resource-000044",
        "start": "2023-02-24T05:28:00.843", "end": "2023-02-24T05:34:31.219"
    },
    {
        "case": "2182", "activity": "Activity 2", "resource": "resource-000024",
        "start": "2023-02-24T05:34:31.219", "end": "2023-02-24T05:47:25.817"
    },
    ...
]
```

If your log files have any of these formats you can run `edm` specifying the log format via the option `--format`:

```shell
$> expert ./log.csv --format csv
```

or

```shell
$> expert ./log.json --format json
```

If you need a different mapping for processing your log files, you can specify it using a JSON file:

```json
{
    "case": "<your case attribute name>",
    "activity": "<your activity attribute name>",
    "resource": "<your resource attribute name>",
    "start": "<your start time attribute name>",
    "end": "<your end time attribute name>"
}
```

Then, you can then run `expert` with the option `--mapping MAPPING_FILE` to use your custom mapping:

```shell
$> expert ./log.csv --format csv --mapping ./my_custom_mapping.json
```

Run `expert --help` to check the additional options:

```shell
$> expert --help

usage: expert [-h] [-f FORMAT] [-m MAPPING_FILE] [-t TIMEFRAME] [-a ALPHA] [-v] LOG_FILE

Explainable Performance Drift is an algorithm for finding actionable causes for drifts in the
performance of a process execution. For this, the cycle time of the process is monitored, and,
if a change is detected in the process performance, the algorithm finds the actionable causes
for the change.

positional arguments:
  LOG_FILE                                    The event log, in CSV or JSON format.

options:
  -h, --help                                  show this help message and exit
  -f FORMAT, --format FORMAT                  specify the event log format
  -m MAPPING_FILE, --mapping MAPPING_FILE     provide a custom mapping file
  -t TIMEFRAME, --timeframe TIMEFRAME         provide a timeframe size, in days, used
                                              to define the reference and running models.
  -a ALPHA, --alpha ALPHA                     specify the confidence for the statistical tests
  -v, --verbose                               enable verbose output. High verbosity level can
                                              drastically decrease expert performance

expert is licensed under the Apache License, Version 2.0

```

## Using `expert` as a Python package

Aside of providing an executable command, `expert` can be fully customized by using it as a Python package.
If you use poetry you can install `expert` directly from git:

```shell
$> poetry add "https://gitlab.citius.usc.es/ProcessMining/explainable-performance-drift.git"

```

When using it as a package, the drift detection algorithm can be located at `expert.drift.detect_drift`.

# How can I...?

## ...read a log from different source than CSV or JSON?

`expert` provides you with all the utilities needed to read CSV and JSON files in a performant way.
However, we are aware that your logs may be in a different format. You may even want to read your logs from a database
or message queue! Don't worry, we've got you covered. The representation we use for logs in expert is a
simple `Iterator`
object, so you can implement any data source you need, and as long as it returns an `Iterator` of `expert.model.Event`
objects you shouldn't have any problems. As a reference, you can check the implementations
from `expert.input.csv.read_csv_log`
and `expert.input.json.read_json_log`, which are implemented using generators so the memory consumption is reduced.

## ...check the performance for only a part of my process?

In `expert` you can specify exactly which activities mark the start and the end of the subprocess that you want to
monitor.
To do that, you just have to specify your initial and final activities when calling `expert.drift.detect_drift`, and the
algorithm will deal with the rest!

## ...filter some of my events?

When using `expert` as a Python package, you can provide some filters to the `expert.drift.detect_drift` method.
By default, `expert` provides you some filters that can be used, like filtering all events without an assigned resource
or those whose duration is 0.
You can extend this and implement any filter you need. The signature for the filtering functions receives an event
instance and must return a boolean indicating if that event should be kept or discarded.
In CLI mode the filters are not available, so you will have to preprocess your log files before using `expert`.