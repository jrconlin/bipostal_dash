from pyramid.config import Configurator

from mozsvc.config import load_into_settings

from bipostal.resources import Root
from bipostal.storage import configure_from_settings


def main(global_config, **settings):
    config_file = global_config['__file__']
    load_into_settings(config_file, settings)

    config = Configurator(root_factory=Root, settings=settings)

    config.registry['storage'] = configure_from_settings(
        'storage', settings['config'].get_map('storage'))

    # Adds authorization.
    config.include("pyramid_multiauth")

    # Adds cornice.
    config.include("cornice")

    # Adds Mozilla default views.
    config.include("mozsvc")

    # Adds application-specific views.
    config.scan("bipostal.views")

    config.add_static_view('/', 'bipostal:backbone/',
                           permission='authenticated')

    return config.make_wsgi_app()
