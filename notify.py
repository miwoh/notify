#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
import argparse
import smtplib
import logging
import datetime
import sys
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
if sys.version_info > (3, 0):
    from configparser import ConfigParser
else:
    from ConfigParser import ConfigParser


class Project(object):

    _revision = ""
    _author = ""

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

    def getsvninfos(self):
        svnlookproc = subprocess.Popen(["svnlook", "author", "-r", args.rev, args.repo],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = svnlookproc.communicate()
        if svnlookproc.returncode != 0:
            log.error("Error determining author. Exiting...")
            return 99001
        else:
            self._author = str(out).rstrip()
            return 0

    def buildmsgbody(self):
        if self.getsvninfos() != 0:
            return 99001
        # TODO: Add timezone, somehow, since python thinks that's useless information apparently
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " CET"
        bodyfile = "htmlbody"
        body = open(bodyfile).read()
        html = body.format(mailsubject=self._mailsubject, url=self._URL, name=self._name,
                           author=self._author, date=date)
        '''html = """\
        <html>
          <head></head>
          <body>
            <p>Test Mail<br>
               Python Test Mail<br>
               Here is the <a href="http://www.python.org">link</a> you wänted.
            </p>
          </body>
        </html>
        """'''
        text = "Python test mäil"
        part1 = MIMEText(text, 'plain', 'utf-8')
        part2 = MIMEText(html, 'html', 'utf-8')
        self._mailmsg.attach(part1)
        self._mailmsg.attach(part2)
        #self.mail()

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
        commitfile = open("commitfile", "w")
        # DEBUG Output
        log.debug("These were the found commits:")
        for value in commits:
            log.debug("'%s'" % value.split(" "))
        # creates an project object for each unique project found in the commit file
        for section in confile.getsections():
            createdprojects = []
            commitfile.write("<table>\n")
            # TODO: Put that somewhere else, it shouldnt be in Configfile
            for commit in commits:
                action = commit.split(" ")[0]
                commit = commit.split(" ")[-1]
                if action.upper() == "A":
                    commitfile.write("<tr style='mso-yfti-irow:0;mso-yfti-firstrow:yes'><td style='padding:4.0pt 4.0pt 4.0pt 4.0pt'><p>Added</p></td>\n")
                elif action.upper() == "U":
                    commitfile.write("<tr style='mso-yfti-irow:0;mso-yfti-firstrow:yes'><td style='padding:4.0pt 4.0pt 4.0pt 4.0pt'><p>Modified</p></td>\n")
                elif action.upper() == "D":
                    commitfile.write("<tr style='mso-yfti-irow:0;mso-yfti-firstrow:yes'><td style='padding:4.0pt 4.0pt 4.0pt 4.0pt'><p>Deleted</p></td>\n")
                if commit.endswith("/"):
                    commitfile.write("<td style='padding:4.0pt 4.0pt 4.0pt 4.0pt'><p>&lt;Directory&gt;</p></td>\n")
                else:
                    commitfile.write("<td style='padding:4.0pt 4.0pt 4.0pt 4.0pt'><p>" + commit.split("/")[-1] + "</p></td>\n")
                if section in commit and section not in createdprojects:
                    proj = Project(section)
                    createdprojects.append(section)
                    if proj.buildmsgbody() != 0:
                        return 99001
            commitfile.write("</table>\n")


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
    parser.add_argument(
        "-r",
        "--revision",
        action="store",
        dest="rev",
        metavar="",
        required=True,
        help="Revision of the current commit (required).")
    parser.add_argument(
        "-R",
        "--repository",
        action="store",
        dest="repo",
        metavar="",
        required=True,
        help="Repository to which the current commit wrote (required).")
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
