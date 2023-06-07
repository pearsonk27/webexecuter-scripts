"""Task runner for webexecuter_scripts"""
import logging
import subprocess
import os
import smtplib
import ssl
from logging.handlers import RotatingFileHandler
import git

LOG_FILE = "/var/log/webexecuter/server-deploy.log"
REPO_PATH = "/srv/git/webexecuter-server"

logging.basicConfig(
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s - LineNo %(lineno)d - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=20, backupCount=5)],
)


def refresh():
    """Automated deployment of the webexecuter server"""
    # If the local repo is behind the remote repo, pull and deploy
    if local_repo_is_behind():
        do_deployment()
        restart_service()


def send_deployment_message(std_out, std_err):
    """Function for sending deployment message"""
    port = os.getenv("AUTOMATION_EMAIL_PORT")
    smtp_server = os.getenv("AUTOMATION_EMAIL_SMTP_SERVER")
    sender_email = os.getenv("AUTOMATION_EMAIL_ACCOUNT")
    receiver_email = os.getenv("AUTOMATION_EMAIL_RECIPIENT")
    password = os.getenv("AUTOMATION_EMAIL_PASSWORD")

    message = f"""\
Subject: Webexecuter Server Deployment

Stdout: {std_out}

Stderr: {std_err}"""

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


def local_repo_is_behind():
    """Determine if a git pull and deployment is necessary"""
    repo = git.Repo(REPO_PATH)
    status = repo.git.status()

    logging.info("Repo status: %s", status)

    return "Your branch is behind" in status


def do_deployment():
    """Run the mvn command and inform the developer about the status"""
    logging.info("Pulling down the remote branch")
    repo = git.Repo(REPO_PATH)
    repo.remotes.origin.pull()
    logging.info("Running maven to deploy")
    proc = subprocess.Popen(
        ["./mvnw clean package"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=REPO_PATH,
    )
    out, err = proc.communicate()
    logging.info("Maven stdout: %s", out.decode("latin-1"))
    logging.info("Maven stderr: %s", err.decode("latin-1"))

    send_deployment_message(out, err)


def restart_service():
    """Need to restart the service after the jar has been updated"""
    proc = subprocess.Popen(
        ["/srv/git/webexecuter-server/src/main/resources/restart.sh"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )
    out, err = proc.communicate()
    logging.info("Service Restart stdout: %s", out.decode("latin-1"))
    logging.info("Service Restart stderr: %s", err.decode("latin-1"))
