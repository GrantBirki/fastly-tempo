# Fastly to Insights 🚀

[![security-checks Actions Status](https://github.com/grantbirki/fastly-to-insights/workflows/security-checks/badge.svg)](https://github.com/grantbirki/fastly-to-insights/actions) [![python-tests Actions Status](https://github.com/grantbirki/fastly-to-insights/workflows/python-tests/badge.svg)](https://github.com/grantbirki/fastly-to-insights/actions) [![docker-build Actions Status](https://github.com/grantbirki/fastly-to-insights/workflows/docker-build/badge.svg)](https://github.com/grantbirki/fastly-to-insights/actions) [![codeQL Actions Status](https://github.com/grantbirki/fastly-to-insights/workflows/codeQL/badge.svg)](https://github.com/grantbirki/fastly-to-insights/actions)

Get all your Fastly metrics into New Relic with ease!

This is based off the New Relic blessed way to get your Fastly metrics into Insights, packaged as a Docker container image for ease of use!

In order to use the Fastly to Insights Docker image, you will need an active New Relic account with Insights, an active Fastly account with Read access, a New Relic Insights Insert key and a Fastly API Key.

## Dashboard

Here is an example of a 4xx alert dashboard that can be created in New Relic from the `Fastly to Insights` container:

![New Relic Dashboard with Fastly Metrics](assets/img/panel.png)

## Quick Start

Grab the image from [DockerHub](https://hub.docker.com/r/grantbirki/fastly-to-insights) 🐳

### Using Docker-Compose (Preferred)

Using Docker-Compose to run this image is extremely easy.

1. Create a file named `creds.env` at the root of this repo with the following contents:

    ```dosini
    INSERT_KEY=XXXXXXXXXXXXXX
    ACCOUNT_ID=#######
    FASTLY_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXX
    ```

2. Add your services to `config.env`

    ```dosini
    ...
    SERVICES=ServiceName1:ServiceId1 ServiceName2:ServiceId2 ...
    ```

3. Run: `make run`

4. ✔️ Log into New Relic and view your logs!

### Using Docker

1. Build: `docker build -t fastly-to-insights .`
2. Run:

    ```#!/bin/bash
    $ docker run \
    -e ACCOUNT_ID='yourNewRelicAccountId' \
    -e FASTLY_KEY='yourFastlyKey' \
    -e INSERT_KEY='yourNewRelicInsertKey' \
    -e SERVICES='ServiceId1 ServiceId2 ...' \
    fastly-to-insights
    ```

## How to use this image

Before you get started, make sure that you have a [Fastly API Key](https://docs.fastly.com/guides/account-management-and-security/using-api-tokens) and a [New Relic Insert Key](https://docs.newrelic.com/docs/insights/insights-data-sources/custom-data/insert-custom-events-insights-api#register).

The Fastly to Insights image is configured by environment variables. These are mandatory:

* `ACCOUNT_ID`
* `FASTLY_KEY`
* `INSERT_KEY`
* `SERVICES`

These are optional:

* `SILENT` - Print output True/False
* `INTERVAL` - Interval in seconds to poll data from Fastly

### Fastly Services

You have two options for passing in Fastly Services to the Docker container.

1. Passing in only the **ServiceId**
2. Passing in both the **ServiceName** and the **ServiceId**

Note: In both examples, one serivce has millions of 200s and the other has none.

#### 1. ServiceId

If you are just using the ServiceId method, `SERVICES` needs to be a string with the ids of the Fastly services you want to see data for in Insights, separated by a space. I know that's not ideal. A limitation of Fastly is that you have to query one service at a time, so I chose to create an array of service ids and loop through them to query Fastly. A limitation of Docker is that you can't pass an array via the command line, so I chose to split a string on " ". If you have a better idea, I would love to hear it - please contribute!

Example:

```#!/bin/bash
$ docker run \
  -e ACCOUNT_ID='yourNewRelicAccountId' \
  -e FASTLY_KEY='yourFastlyKey' \
  -e INSERT_KEY='yourNewRelicInsertKey' \
  -e SERVICES='ServiceId1 ServiceId2 ...' \
  fastly-to-insights
```

You may optionally add `-e SILENT=True` or `-e INTERVAL=<time in seconds>` for custom configuration.

Here is what this will look like in New Relic:

![ServieId Only Image](assets/img/service-id-only.png)

#### 2. ServiceId + ServiceName

If you want to map your ServiceId to a friendly name use this method. This method is the same as `1. ServiceId` above with one minor change. With this method `SERVICES` needs to be a string with the `<NameOfService>:<ServiceId>` of the Fastly services you want to see data for in Insights, separated by a space (Example below).

The benefit to using this method is you can name the service whatever you want. It could be a friendly name, the actual name of the service in Fastly, or your favorite planet.

Example:

```#!/bin/bash
$ docker run \
  -e ACCOUNT_ID='yourNewRelicAccountId' \
  -e FASTLY_KEY='yourFastlyKey' \
  -e INSERT_KEY='yourNewRelicInsertKey' \
  -e SERVICES='NameOfService1:ServiceId1 NameOfService2:ServiceId2 ...' \
  fastly-to-insights
```

You may optionally add `-e SILENT=True` or `-e INTERVAL=<time in seconds>` for custom configuration.

Here is what this will look like in New Relic:

![ServieId Only Image](assets/img/friendly-service-name.png)

Note: You can mix `method 1` and `method 2` together. In the `SERVICES` variable. I would not recommend doing this though.

## New Relic Queries to View Data

Here are some helpful queries in New Relic to start viewing your metrics:

* 2xx Status codes by service

    ```sql
    SELECT average(status_2xx) FROM LogAggregate since 30 minutes ago TIMESERIES 15 minutes facet service
    ```

* 3xx Status codes by service

    ```sql
        SELECT average(status_3xx) FROM LogAggregate since 30 minutes ago TIMESERIES 15 minutes facet service
    ```

* 4xx Status codes by service

    ```sql
    SELECT average(status_4xx) FROM LogAggregate since 30 minutes ago TIMESERIES 15 minutes facet service
    ```

* 5xx Status codes by service

    ```sql
    SELECT average(status_5xx) FROM LogAggregate since 30 minutes ago TIMESERIES 15 minutes facet service
    ```

* The number of cache hits by service

    ```sql
    SELECT average(hits) FROM LogAggregate since 30 minutes ago TIMESERIES 15 minutes facet service
    ```

* The number of cache misses by service

    ```sql
    SELECT average(miss) FROM LogAggregate since 30 minutes ago TIMESERIES 15 minutes facet service
    ```

* The total amount of time spent processing cache misses (in seconds)

    ```sql
    SELECT average(miss_time) FROM LogAggregate since 30 minutes ago TIMESERIES 15 minutes facet service
    ```

To see more info on these queries, check out the blog post by New Relic [here](https://blog.newrelic.com/engineering/monitor-fastly-data/).

## Contributing

You are welcome to send pull requests to this repo. All and any contributors are welcome.

## More Information

For more information on the Fastly Real-Time Analytics API, look [here](https://docs.fastly.com/api/analytics).

For more information on the New Relic Insights API, look [here](https://docs.newrelic.com/docs/insights/insights-data-sources/custom-data/insert-custom-events-insights-api).

This project is provided AS-IS WITHOUT WARRANTY OR SUPPORT, although you can report issues and contribute to the project.

## JavaScript version

This project is the python implementation of the original [Fastly-to-Insights](https://github.com/newrelic/fastly-to-insights) project. Check out the source project to see how this one differs and if the Python version is right for you.
