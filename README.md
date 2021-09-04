# Learning pydantic with a simple actors json file.

This repository explores methods for managing and migrating data across versions using pydantic models.

## Overview

In [tests/testresources](tests/testresources) there are several versioned copies of the actor-data.json file.
Each copy has a different structure.
This structure is the file's schema.
The schema is modeled in [src/aktorz/model](src/aktorz/model).

Each tag/branch/version/whatever of this repository represents a change to the data's schema. As such, the [.bumpversion.cfg](.bumpversion.cfg) is an integral part of the solution and is configured to update [src/aktorz/model/versions.py](src/aktorz/model/versions.py).

The point of this repository (beyond the obvious goal of learning pydantic) is to extend the data models to migrate the data as the model (schema) evolves. This is not unlike ORM database schema migration where our backend is a simple json file.

## Supporting New Schema Versions

1. bumpversion

## Quick Start


## Testing

Install & use tox:

    ./tox.sh

Update requirements.txt and dev-requirements.txt:

    ./tox.sh -e deps

Reformat the code to make it pretty:

    ./tox.sh -e fmt
