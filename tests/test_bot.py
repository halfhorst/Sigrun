import os
from unittest import mock

import pkg_resources
import pytest
from sigrun.bot import Sigrun


@pytest.fixture(autouse=True)
def mock_credentials():
    with mock.patch("sigrun.bot.Sigrun.get_credentials"):
        yield


@pytest.fixture()
def MockDiscordConnection():
    return mock.Mock()


@pytest.fixture()
def MockInteractionData():
    return mock.Mock()


def test_server_manipulation():
    sigbot = Sigrun()
    mock.patch.object(sigbot,
                      "server_script",
                      pkg_resources.resource_filename(
                          "sigrun",
                          "scripts/test_run.sh"))
    mock.patch.object(sigbot,
                      "update_script",
                      pkg_resources.resource_filename(
                          "sigrun",
                          "scripts/test_update.sh"))

    sigbot.start_server()
    assert sigbot.pid_server is not None
    sigbot.stop_server()
