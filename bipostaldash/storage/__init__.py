from pyramid.util import DottedNameResolver


def configure_from_settings(object_name, settings):
    config = dict(settings)
    cls = DottedNameResolver(None).resolve(config.pop('backend'))
    return cls(**config)
