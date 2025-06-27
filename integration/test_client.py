# Copyright (c) 2016 Canonical Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json
import os
import threading
import time
import unittest

from websockets.sync.client import ClientConnection
from ws4py.client import WebSocketBaseClient

import pylxd
from integration.testing import IntegrationTestCase
from pylxd import exceptions
from pylxd.client import EventType


class TestClient(IntegrationTestCase):
    """Tests for `Client`."""

    def test_authenticate(self):
        client = pylxd.Client("https://127.0.0.1:8443/")

        if client.has_api_extension("explicit_trust_token"):
            secret = os.getenv("LXD_TOKEN")
        else:
            secret = "password"

        self.assertFalse(client.trusted)

        client.authenticate(secret)

        self.assertTrue(client.trusted)

    def test_authenticate_with_project(self):
        if self.client.has_api_extension("explicit_trust_token"):
            self.skipTest(
                "Required LXD support for password authentication not available!"
            )

        try:
            client = pylxd.Client("https://127.0.0.1:8443/", project="test-project")
        except exceptions.ClientConnectionFailed as e:
            message = str(e)
            if message == "Remote server doesn't handle projects":
                self.skipTest(message)
            raise

        if client.has_api_extension("explicit_trust_token"):
            secret = os.getenv("LXD_TOKEN")
        else:
            secret = "password"

        client.authenticate(secret)
        self.assertEqual(client.host_info["environment"]["project"], "test-project")

    def _provoke_event(self):
        time.sleep(1)
        self.client.instances.all()  # provoke an event

    @unittest.skip("Broken with websockets")
    def test_events_default_client(self):
        events_ws_client = self.client.events()

        self.assertTrue(issubclass(type(events_ws_client), ClientConnection))
        self.assertEqual(events_ws_client.protocol.wsuri.resource_name, "/1.0/events")

        receiver = threading.Thread(target=self._provoke_event)
        receiver.start()

        message = events_ws_client.recv()
        receiver.join()

        self.assertEqual(len(events_ws_client.messages), 1)
        self.assertEqual(type(events_ws_client.messages[0]), dict)
        self.assertEqual(json.loads(message), events_ws_client.messages[0])
        self.assertEqual(events_ws_client.messages[0]["type"], EventType.Logging.value)

        events_ws_client.close()

    @unittest.skip("Broken with websockets")
    def test_events_filters(self):
        for eventType in EventType:
            if eventType != EventType.All:
                events_ws_client = self.client.events(event_types=[eventType])

                self.assertEqual(
                    events_ws_client.protocol.wsuri.resource_name,
                    f"/1.0/events?type={eventType.value}",
                )

                events_ws_client.close()

    @unittest.skip("Broken with websockets")
    def test_events_provided_client(self):
        events_ws_client = self.client.events(websocket_client=ClientConnection)

        self.assertEqual(type(events_ws_client), ClientConnection)
        self.assertEqual(events_ws_client.protocol.wsuri.resource_name, "/1.0/events")

        receiver = threading.Thread(target=self._provoke_event)
        receiver.start()

        message = events_ws_client.recv()
        receiver.join()

        self.assertEqual(type(message), str)
        self.assertEqual(json.loads(message)["type"], EventType.Logging.value)

        events_ws_client.close()

    @unittest.skip("Broken with websockets")
    def test_events_ws4py_client(self):
        events_ws_client = self.client.events(websocket_client=WebSocketBaseClient)

        self.assertEqual(type(events_ws_client), WebSocketBaseClient)
        self.assertEqual(events_ws_client.resource, "/1.0/events")

        events_ws_client.connect()
        events_ws_client.close()
