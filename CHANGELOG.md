# Managing and Migrating Data with pydantic

---


# v?.?.?

---

# v0.1.2-rc1

---

---

# v0.1.1

## Functional changes

- [bumpversion config](.bumpversion.cfg) improvements
- Added `Rules` section to [README.md](README.md)
- [loader](src/aktorz/model/loader.py)
  - better handling of input/model version
  - improved documentation
  - added `module()` method
- [schema_version](src/aktorz/model/schema_version.py)
  - refactored to "has-a" semver versus "is-a" semver
  - legitimize the version prefix
- [base_test](tests/base_test.py)
  - extracted to provide common fixtures & tests to all suites

## Model changes

- CastMember
  - field changes
    - name is now optional
      constructed from first/last_name if missing
  - new fields (optional):
    - first_name
    - last_name
  - new methods
    - validate_name() sets `name` from first/last_name if missing
- Exporter
  A new object in the model module specifically for exporting the model in different format versions.
- Movie
  - field changes
    - budget is now `Optional[conint(ge=0)]`
    - run_time_minutes is now `Optional[conint(ge=0)]`
- MovieId
  - is now `constr(regex=r'[a-z][a-z0-9_]+')`
- PersonId
  - is now `constr(regex=r'[a-z][a-z0-9_]+')`
- Year
  - is now `conint(ge=1850)`

---

# v0.1.0

Initial implementation
