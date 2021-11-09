def finalize_version(v):
    # Remove `-rc#` from a version string.
    assert isinstance(v, str)
    try:
        i = v.index("-rc")
        return v[0:i]
    except ValueError:
        return v
