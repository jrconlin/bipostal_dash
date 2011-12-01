from pyramid.config import Configurator

from mozsvc.config import load_into_settings

from bipostaldash.resources import Root
from bipostaldash.storage import configure_from_settings


def main(global_config, **settings):
    config_file = global_config['__file__']
    load_into_settings(config_file, settings)

    config = Configurator(root_factory=Root, settings=settings)

    config.registry['storage'] = configure_from_settings(
        'storage', settings['config'].get_map('storage'))

    config.registry['auth'] = configure_from_settings (
        'auth', settings['config'].get_map('auth'))

    # Adds authorization.
    config.include("pyramid_multiauth")

    # Adds cornice.
    config.include("cornice")

    # Adds Mozilla default views.
    config.include("mozsvc")

    # Adds application-specific views.
    config.scan("bipostaldash.views")

    config.add_static_view('/', 'bipostaldash:backbone/',
                           permission='authenticated')

    return config.make_wsgi_app()
