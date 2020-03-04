def override_defaults(override, default):
    import json
    result = json.loads(json.dumps(default))

    def merge(onto, _from):
        for key, value in _from.items():
            if (key in onto
                    and isinstance(onto[key], dict)
                    and isinstance(value, dict)):
                merge(onto[key], value)
            else:
                onto[key] = value
    merge(result, override)
    return result


def requires(*task_names):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for task_name in task_names:
                try:
                    assert task_name in kwargs["tasks"]
                except AssertionError:
                    raise AssertionError(f"{task_name} not in tasks")
                except KeyError:
                    raise ValueError("Must pass 'tasks' as a keyword argument")
            return func(*args, **kwargs)
        return wrapper
    return decorator
