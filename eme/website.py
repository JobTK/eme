import logging
from collections import defaultdict
from os.path import join

from flask import Flask
from werkzeug.routing import BaseConverter

from .entities import load_handlers


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

http_verbs = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


class WebsiteApp(Flask):
    jinja_options = Flask.jinja_options.copy()
    #jinja_options.update()

    def __init__(self, config: dict, fbase):
        if len(config) == 0:
            raise Exception("Empty config file provided")
        conf = config['website']
        crou = config['routing']
        chead = config['headers']

        static_folder = join(fbase, conf.get('static_folder', 'public'))
        template_folder = join(fbase, conf.get('template_folder', 'templates'))

        super().__init__('/', static_url_path=conf.get('static_url_path', ''), static_folder=static_folder, template_folder=template_folder)

        # Routing
        self._custom_routes = defaultdict(set)
        self.url_map.converters['regex'] = RegexConverter

        # Socket
        self.host = conf.get('host', '0.0.0.0')
        self.port = conf.get('port')

        # Flags
        self.debug = conf.get('debug') == 'yes'
        #self.testing = conf.get('testing') == 'yes'
        self.develop = conf.get('develop') == 'yes'

        #self.json_encoder = EntityJSONEncoder

        # Logging
        # Logging
        logger = logging.getLogger(conf.get('logprefix', 'eme'))
        logger.setLevel(logging.DEBUG)

        # file log
        fh = logging.FileHandler(conf.get('logfile', join(fbase+'logs.txt')))
        lvl = conf.get('loglevel', 'WARNING')
        fh.setLevel(getattr(logging, lvl))

        # console log
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)

        self.logger = logger

        # Load default controllers
        cdir = join(fbase, conf.get('controllers_dir'))
        self.load_controllers(cdir, index=crou.get('INDEX'))

        @self.after_request
        def after_request(response):
            for name, val in chead.items():
                response.headers[name] = val

            #if hasattr(response, 'api') and response.api:
            #    response.headers['Content-Type'] = 'application/json'
            #response.headers['Referrer-Policy'] = 'no-referrer-when-downgrade'

            return response

    def preset_endpoint(self, new_url, endpoint):
        # strip the verb from the url
        sp = new_url.split(' ')
        prefix = 'GET' if len(sp) == 1 else sp[0].upper()
        new_url = ''.join(sp[1:])

        # force the GET keyword into the endpoint
        controller, method = endpoint.split('.')
        if prefix == 'GET' and method[0:3].lower() != 'get':
            method = prefix.lower() + '_' + method

        # custom routes are a map of {Controller.verb_method -> overridden_url}
        self._custom_routes[controller + '.' + method].add(new_url)

    def preset_endpoints(self, rules):
        for new_url, endpoint in rules.items():
            self.preset_endpoint(new_url, endpoint)

    def load_controllers(self, path=None, index=None):
        print('{0: <7}{1: <20}{2: <20} >    {3}'.format("OPT", "ROUTE", "ENDPOINT", "ACTION"))

        # automatically parses custom
        controllers = load_handlers(self, "Controller", path)

        for controller_name, controller in controllers.items():
            for method_name in dir(controller):
                method = getattr(controller, method_name)

                if method_name.startswith("__") or method_name in ["rws", "server"] or not callable(method):
                    continue

                option = "GET"
                action_name = method_name
                methods = method_name.split('_')

                if methods[0].upper() in http_verbs:
                    option = methods.pop(0).upper()
                    action_name = '_'.join(methods)

                # default route without action is index
                if index == controller_name + '.' + method_name:
                    route = "/"
                elif method_name == "index" or action_name == "":
                    route = "/" + controller_name.lower()
                else:
                    route = "/" + controller_name.lower() + "/" + action_name

                endpoint = controller_name + '.' + option.lower() + '_' + action_name
                #endpoint = option.lower() + '__' + route[1:]
                if endpoint[-1] == '_':
                    endpoint += 'index'

                # check if a custom routing rule has overridden the default one
                if endpoint in self._custom_routes:
                    routes = self._custom_routes[endpoint]
                else:
                    # otherwise there's only one possible route for this endpoint
                    routes = {route}

                if endpoint in self.view_functions:
                    # if endpoint is already configured, we ignore
                    continue

                for route in routes:
                    print('{0: <7}{1: <20}{2: <20} >    {3}'.format(option, route, endpoint, controller_name + "." + method_name))
                    self.add_url_rule(route, endpoint, getattr(controller, method_name), methods=[option])

                #self.view_functions
                #self.url_map

    def start(self):
        self.run(self.host, self.port, threaded=True, debug=self.debug)