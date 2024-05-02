# DidIMissDaBus Python

This project uses the NextBus API to present an API for the Toronto Transit Commission (TTC) routes, stops, and vehicle locations.

## Overview

DidIMissDaBus Python is a Python-based application REST interface that expsoses informations from the NextBus API to provide real-time data on TTC routes, stops, and vehicle locations. This data can be used to determine where a vehicle is on it's route.

The initial goal of this project was to get a better estimate of arrival time for TTC vehicles.  However, it became very apparent that you first need an overview of everything that is occurring before you can start making inferences.

## Features

Rest API to return
- return routes
- stops for a specific route
- vehicle locations for a specific route
- it gets rate limited a lot

## Modules

- `main.py`: Implements the REST API and the main loop that monitors the NextBus API.
- `mathy_module.py`: Implements methods related to distance between stops and where on a route a vehicle is.
- `models_module.py`: Contains Python classes that abstract the transit system data.
- `request_and_parsing_module.py`: Handles all the interaction with the NextBus API and converting it into the models.
- `statesman_module.py`: Holds the current state of the transit system, where every vehicle is, what stops are available, and is what the REST API queries to get info to return, and what the `request_and_parsing_module` updates on every loop.

## Getting Started

To get started with this project, don't, start from scratch but use as much of it as you'd like.

## Contributing

Nahh, no contributions are needed. It's going to wither and become irrelevant eventually.

## License

This project is licensed under the terms of the MIT license.