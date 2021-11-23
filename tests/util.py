def finalize_version(v):
    """
    Remove `-rc#` from a version string.
    A more realistic implementation would convert `v` to a SchemaVersion
    instance and use schema_version.semver.finalize_version().
    """
    assert isinstance(v, str)
    try:
        i = v.index("-rc")
        return v[0:i]
    except ValueError:
        return v
