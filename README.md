# Managing and Migrating Data with pydantic

This repository explores methods for managing and migrating data across versions using pydantic models.

## Overview

In [tests/testresources](tests/testresources) there are several versioned copies of the actor-data.json file.
Each copy has a different structure.
This structure is the file's schema.
The schema is modeled in [src/aktorz/model](src/aktorz/model).

Each tag/branch/version/whatever of this repository represents a change to the data's schema. As such, the [.bumpversion.cfg](.bumpversion.cfg) is an integral part of the solution and is configured to update [src/aktorz/model/versions.py](src/aktorz/model/versions.py).

The point of this repository (beyond the obvious goal of learning pydantic) is to extend the data models to migrate the data as the model (schema) evolves. This is not unlike ORM database schema migration where our backend is a simple json file.

## About Versions

The version tags of this project reflect the data format, they specifically do not reflect the versions (evolution) of the supporting code (e.g. -- BaseModel, Loader, etc). The supporting code evolves as necessary to support our ability to load, save, import and export the data as it changes over time.

In retrospect, the `v` prefix for both the version and the version implementation modules should have probably been `f` (e.g. -- format version) and the `v` used to mark milestones of the supporting code. I may go back and refactor along those lines _or_ I may extract the supportting code into a separate library when things mature a bit more.

## Supporting New Schema Versions

1. bumpversion --new-version x.y.z-rc1 patch
2. cp src/aktorz/model/v{current_version}.py src/aktorz/model/v{new_version}.py
3. cp src/tests/test_{current_version}.py src/tests/test_{new_version}.py
4. git add/commit/push
5. Update the new model and its test to implement whatever is required for the new version.
6. bumpversion --new-version x.y.z patch
7. git add/commit/push

## Rules

Follow semver: major.minor.patch\[-rc#\]

Our focus is primarily on consuming a json document of a specified schema version.

Given a document having version D, Model M1 having version V1 and Model M2 having version V2 where all three versions share the same major component (or minor component if major component is zero):
- M1 must be able to directly load documents (via m1.parse_*()) matching its version (V1 == D).
- M1 must be able to read (via Loader) documents writen by recent older models (V1 >= D).
- M1 must be able to create an output document (via Exporter) consumable by recent older models (V1 >= V2, V1 -> D, D <= V2).
- M1 is _not_ required to create a default output document (e.g. - m1.dict()) consumable by any older models (V1 > V2).
- M2 is _not_ required to consume (in any way) a document created by a newer model (V2 < D).

No compatibility is required or assumed when major components differ (or minor components if major is zero).

Through custom Loader/Exporter implementations it is permissible (but not required) for implementation modules to provide read/write capability beyond the basic requirements stated here.

### Major

- Any breaking changes are allowed.

### Minor

**If Major = 0**
- Any breaking changes are allowed.

**If Major > 0**
- Must comply with all Major rules.

### Patch

**If Major = 0**

- Must be able to read older document versions within the same Minor version.
- May or may not be able to read older document versions within the same Minor version.
- Any 0.m.pj model must be able to read any 0.m.pi document when pj >= pi.
  e.g. -- A model 0.1.5 must be able to read any 0.1.2 document.
- Any 0.m.pi model may or may not be able to read any 0.m.pj document when pj > pi.
  e.g. -- A model 0.1.2 may or may be able to read any 0.1.5 document.
- Must be able to create an optional output document that is consumable by older model versions within the same Minor version.
  e.g. -- A model 0.1.5 must provide the option of creating a 0.1.2 document.

Can add:
- New optional fields.

Can change:

Can remove:
- Optional fields (but still be able to consume older documents where these are present).

**If Major > 0**
- Must comply with all Major and Minor rules.

## Testing

Install & use tox:

    ./tox.sh

Update requirements.txt and dev-requirements.txt:

    ./tox.sh -e deps

Reformat the code to make it pretty:

    ./tox.sh -e fmt
