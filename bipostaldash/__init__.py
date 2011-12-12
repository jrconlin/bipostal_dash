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

    config.registry['dash_auth'] = configure_from_settings (
        'dash_auth', settings['config'].get_map('dash_auth'))

    config.registry['config'] = settings['config'].get_map()

    # Adds authorization.
    config.include("pyramid_multiauth")

    # Adds cornice.
    config.include("cornice")

    # Adds beaker.
    config.include("pyramid_beaker")

    # Adds Mozilla default views.
    config.include("mozsvc")

    # Adds application-specific views.
    config.scan("bipostaldash.views")

    config.add_static_view('/', 'bipostaldash:backbone/',
            # permission="authenticated"
            )

    return config.make_wsgi_app()
