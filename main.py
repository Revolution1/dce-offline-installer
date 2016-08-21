import logging
import sys
from inspect import getdoc

from utils import DocoptCommand, NoSuchCommand, load_json_from, parse_doc_section

log = logging.getLogger(__name__)

console_handler = logging.StreamHandler(sys.stderr)


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)
    # Disable requests logging
    logging.getLogger("requests").propagate = False


class TopLevelCommand(DocoptCommand):
    """
    DaoCloud Enterprise Offline Installer

    Usage:
      doi [options] [COMMAND] [ARGS...]

    Options:
      -h, --help  Show this help information and exit.

    Commands:
      list           List available versions of DCE, Docker and Docker-compose.
      prepare        Download packages and generate install script.
      install        Install and configure the DCE Cluster.
      version        Show the DCE version information.
    """
    base_dir = '.'

    def perform_command(self, options, handler, command_options):
        handler(command_options)
        return

    def docopt_options(self):
        options = super(TopLevelCommand, self).docopt_options()
        options['version'] = 'v0.1'
        return options

    def prepare(self, options):
        """
        Download packages and generate install script.

        Usage:
          prepare [options] [ARGS...]

        Options:
          -h, --help            Show this help information and exit.
          -c <file>             Load config from file.
          --dce <version>       Version of DCE.
          --docker <version>    Version of docker.
          --lsb <lsb:version>   Version of Linux distribution.
          --compose <version>   Version of docker-compose.

        If a version is not specified, the latest version of it will be prepared.
        """
        config_file = options.get('-c')
        dce = options.get('--dce')
        docker = options.get('--docker')
        lsb = options.get('--lsb')
        lsb_version = None
        compose = options.get('--compose')
        config = {}
        if config_file:
            try:
                config = load_json_from(config_file)
            except Exception as e:
                log.error('Load config file fail: %s' % e)
                exit(1)
        dce and config.update({'dce': dce})
        compose and config.update({'compose': compose})
        if lsb:
            split = lsb.split(':')
            if len(split) == 2:
                lsb = split[0]
                lsb_version = split[1]
        _d = {}
        docker and _d.update({'version': docker})
        lsb and _d.update({'lsb': lsb})
        lsb_version and _d.update({'lsb_version': lsb_version})
        if lsb or docker:
            if 'docker' in config:
                config['docker'].update(_d)
            else:
                config['docker'] = _d
        from preapre import prepare
        prepare(config)

    def install(self, options):
        """
        Copy packages to nodes, install Docker and DCE

        Usage:
          install [options] [ARGS...]

        Options:
          -h, --help  Show this help information and exit.

        """
        print('install')

    def list(self, options):
        """
        List available versions of DCE, Docker and Docker-compose

        Usage:
          list
          list dce|docker|compose

        Options:
          -h, --help  Show this help information and exit.
        """
        print(options)

    def version(self, options):
        """
        Show the version information

        Usage: version
        """
        print('v0.1')


def main():
    setup_logging()
    try:
        command = TopLevelCommand()
        command.sys_dispatch()
    except NoSuchCommand as e:
        commands = "\n".join(parse_doc_section("commands:", getdoc(e.supercommand)))
        log.error("No such command: %s\n\n%s", e.command, commands)
        sys.exit(1)


if __name__ == '__main__':
    main()
