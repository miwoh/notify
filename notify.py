#!/usr/bin/python
# -*- coding: utf-8 -*-
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


class Project(object):

    _path = ""
    _URL = ""
    _name = ""
    _mailhost = ""
    _mailport = ""
    _mailsender = ""
    _mailpass = ""
    _mailrecipients = ""
    _mailsubject = ""
    _mailmsg = ""

    def __init__(self, projectname):
        self._name = projectname
        self._URL = confile.getvalue("global", "urlprefix") + self._name
        self._mailhost = confile.getvalue("global", "smtphost")
        self._mailport = confile.getvalue("global", "smtpport")
        self._mailsender = confile.getvalue("global", "smtpuser")
        self._mailpass = confile.getvalue("global", "smtppassword")
        self._mailrecipients = confile.getvalue(self._name, "mailrecipients")
        self._mailsubject = confile.getvalue(self._name, "mailsubject")
        self._mailmsg = MIMEMultipart('alternative')

    def buildmsgbody(self):
        html = """\
        <html>
          <head></head>
          <body>
            <p>Test Mail<br>
               Python Test Mail<br>
               Here is the <a href="http://www.python.org">link</a> you wänted.
            </p>
          </body>
        </html>
        """
        text = "Python test mäil"
        part1 = MIMEText(text, 'plain', 'utf-8')
        part2 = MIMEText(html, 'html', 'utf-8')
        self._mailmsg.attach(part1)
        self._mailmsg.attach(part2)
        self.mail()

    def mail(self):
        fromaddr = self._mailsender
        toaddr = self._mailrecipients
        self._mailmsg['From'] = fromaddr
        self._mailmsg['To'] = toaddr
        self._mailmsg['Subject'] = self._mailsubject
        server = smtplib.SMTP(self._mailhost, self._mailport)
        server.ehlo()
        server.starttls()
        server.ehlo()
        # TODO: en/decrypt plain password
        server.login(self._mailsender, self._mailpass)
        server.sendmail(fromaddr, toaddr, self._mailmsg.as_string())
        server.quit()


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
        except Exception as e:
            # TODO: ConfigParserException
            e = str(e).splitlines()[0]
            log.fatal("ConfigParser Error: " + str(e))
            return 1

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

        # Debug Output for all sections and values found in them
        for section in self._conf:
            log.debug("Section from the config file: '%s'" % section)
            options = []
            for value in self._conf[section]:
                options.append(value)
            log.debug("Options in this section: %s" % str(options))
        return 0

    def getsections(self):
        sections = []
        for section in self._conf:
            sections.append(section)
        return sections

    def getvalue(self, section, option):
        """ Returns the chosen option from the chosen section

        Attributes:
            section (str): section from which to read
            option (str): option to read from the section

        """
        requiredvalues = ["smtphost", "smtpport", "smtppassword", "mailprefix", "urlprefix"]
        try:
            return self._conf[section][option]
        except KeyError:
            for value in requiredvalues:
                if option == value:
                    log.fatal("Option '%s' not found in '%s'. It is required. Exiting...")
                    return 1
                else:
                    log.warning("Option '%s' not found in '%s'." % (option, section))

    @staticmethod
    def createprojects(commitfilepath):
        commits = open(commitfilepath).read().splitlines()
        # DEBUG Output
        log.debug("These were the found commits:")
        for value in commits:
            log.debug("'%s'" % value.split(" "))
        # creates an project object for each unique project found in the commit file
        for section in confile.getsections():
            createdprojects = []
            for commit in commits:
                commit = commit.split(" ")[-1]
                if section in commit and section not in createdprojects:
                    proj = Project(section)
                    createdprojects.append(section)
                    proj.buildmsgbody()


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
    parser.add_argument(
        "-C",
        "--commit",
        action="store",
        dest="commitfile",
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
    logfile = os.path.join(logdir, "notify.log")
    try:
        logging.basicConfig(filename=logfile,
                            format="%(asctime)s %(levelname)-8s %(module)-6s %(message)s",
                            level=os.environ.get("LOGLEVEL", "DEBUG"))
    except IOError as e:
        sys.stderr.write("Error creating log file: " + str(e))
        return 1
    log = logging.getLogger("SVN Notification Log")
    log.debug("#" * 20 + " D E B U G M O D E " + "#" * 20)
    return 0


def main():
    return 0


if __name__ == "__main__":
    if init_log() == 1:
        sys.stderr.write("Critical error while creating log file. Exiting...")
        sys.exit(1)
    args = get_cl_options()
    confile = Configfile(args.configfile)
    confile.importvalues()
    confile.createprojects(args.commitfile)
    sys.exit(main())
