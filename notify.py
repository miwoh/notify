import argparse
import smtplib
import logging
import sys
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
if sys.version_info > (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser


class Configfile(object):
    """ An object for the configuration file

    Precondition:
        - a configuration file with valid values

    Attributes:
        _path (str): full path (including filename) to the configuration file
        _conf (dir): read settings from the configuration file

    """

    _conf = {}

    def __init__(self, path):
        self._path = path

    @property
    def exists(self):
        """ Returns True if the (configuration) file exists at the given path """
        if os.path.isfile(self._path):
            return True
        else:
            log.critical("Configuration file doesn't exist")
            return False

    def importvalues(self):
        """ Imports the values from the configuration file into a dictionary variable """
        try:
            parser = ConfigParser()
            parser.read(self._path)
            self._conf = {section: dict(parser.items(section)) for section in parser.sections()}
            if self._conf == {}:
                log.fatal("No values found in the configuration file.")
                return 1
            foundglobal = False
            for section in self._conf.keys():
                if section == "global":
                    foundglobal = True
            if foundglobal is False:
                log.fatal("The 'global' section could not be found in the config file. It is required.")
                return 1
        except Exception as e:
            e = str(e).splitlines()[0]
            log.fatal("ConfigParser Error: " + str(e))
            return 1
        return 0

    def getvalue(self, section, option):
        """ Returns the chosen option from the chosen section

        Attributes:
            section (str): section from which to read
            option (str): option to read from the section

        """
        try:
            return self._conf[section][option]
        except KeyError:
            if ("svnadmin" in option) or ("svn" in option):
                log.warning("'%s' not found in '%s'. Using default." % (option, section),
                            extra={"currentname": "ConfigFile"})
            else:
                log.warning("The '%s' option could not be found in section '%s'." % (option, section),
                            extra={"currentname": "ConfigFile"})
                return 1


def get_cl_options():
    """ Builds the parser and returns the given cl argument/s """
    parser = argparse.ArgumentParser(
        description="Python SVN Notification Script.")
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        dest="configfile",
        metavar="",
        required=True,
        help="Full path to the configuration file (required).")

    arguments = parser.parse_args()
    return arguments


def init_log():
    global log
    logdir = os.path.join(os.path.dirname(__file__), "log")
    if not os.path.exists(logdir):
        try:
            os.makedirs(logdir)
        except OSError as e:
            sys.stderr.write("Error creating log directory: " + str(e))
            return 1
    logfile = os.path.join(logdir, "dump.log")
    try:
        logging.basicConfig(filename=logfile,
                            format="%(asctime)s %(levelname)-8s %(currentname)-10s %(message)s",
                            level=os.environ.get("LOGLEVEL", "DEBUG"))
    except IOError as e:
        sys.stderr.write("Error creating log file: " + str(e))
        return 1
    log = logging.getLogger("SVN Notification Log")
    return 0


def main():
    return 0


if __name__ == "__main__":
    if init_log() == 1:
        sys.stderr.write("Critical error while creating log file. Exiting...")
        sys.exit(1)
    args = get_cl_options()
    confile = Configfile(args.configfile)
    sys.exit(main())
