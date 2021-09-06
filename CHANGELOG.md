# Managing and Migrating Data with pydantic

---

# v0.1.1

- CastMember
  - field changes
    - name is now optional
      constructed from first/last_name if missing
  - new fields (optional):
    - first_name
    - last_name
  - new methods
    - validate_name() sets `name` from first/last_name if missing
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
