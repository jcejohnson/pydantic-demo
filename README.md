# Managing and Migrating Data with pydantic

This repository explores methods for managing and migrating data across versions using pydantic models.

## Overview

In [tests/testresources](tests/testresources) there are several versioned copies of the actor-data.json file.
Each copy has a different structure.
This structure is the file's schema.
The schema is modeled in [src/aktorz/model](src/aktorz/model).

Each tag/branch/version/whatever of this repository represents a change to the data's schema. As such, the [.bumpversion.cfg](.bumpversion.cfg) is an integral part of the solution and is configured to update [src/aktorz/model/versions.py](src/aktorz/model/versions.py).

The point of this repository (beyond the obvious goal of learning pydantic) is to extend the data models to migrate the data as the model (schema) evolves. This is not unlike ORM database schema migration where our backend is a simple json file.

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

Any given document version M.m1.p1 should be comsumable by any model M.m2.p2 or 0.m.p1 should be comsumable by any model 0.m.p2 where M = 0 when m2 >= m1 and p2 >= p1.

Any given document version M.m1.p1 is not required be comsumable by any model M.m2.p2
when m2 < m1 or when m2 = m1 and p2 < p1.

In other words:
- A model must be able to read documents writen by recent older models.
- A model is _not_ required to create a default output document consumable by any older models.
- A model must be able to create an optional output document consumable by recent older models.

No compatibility is required or assumed when major numbers differ.

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
