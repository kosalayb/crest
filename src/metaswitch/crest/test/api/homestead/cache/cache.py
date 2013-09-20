#!/usr/bin/python

# @file cache.py
#
# Project Clearwater - IMS in the Cloud
# Copyright (C) 2013  Metaswitch Networks Ltd
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version, along with the "Special Exception" for use of
# the program along with SSL, set forth below. This program is distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# The author can be reached by email at clearwater@metaswitch.com or by
# post at Metaswitch Networks Ltd, 100 Church St, Enfield EN2 6BQ, UK
#
# Special Exception
# Metaswitch Networks Ltd  grants you permission to copy, modify,
# propagate, and distribute a work formed by combining OpenSSL with The
# Software, or a work derivative of such a combination, even if such
# copying, modification, propagation, or distribution would otherwise
# violate the terms of the GPL. You must comply with the GPL in all
# respects for all of the code used other than OpenSSL.
# "OpenSSL" means OpenSSL toolkit software distributed by the OpenSSL
# Project and licensed under the OpenSSL Licenses, or a work based on such
# software and licensed under the OpenSSL Licenses.
# "OpenSSL Licenses" means the OpenSSL License and Original SSLeay License
# under which the OpenSSL Project distributes the OpenSSL toolkit software,
# as those licenses appear in the file LICENSE-OPENSSL.

import httplib
import mock
import unittest

from mock import ANY
from twisted.internet import defer
from twisted.python.failure import Failure

from metaswitch.crest.api.homestead.cache.cache import Cache
from metaswitch.crest.api.homestead.cache.db import CacheModel

def MockColumn(name, val):
    m = mock.MagicMock()
    m.column.name = name
    m.column.value = val
    return m

class Result(object):
    def __init__(self, deferred):
        self.callback = mock.MagicMock()
        deferred.addCallback(self.callback)

    def value(self):
        return self.callback.call_args[0][0]

class TestCache(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)

        patcher = mock.patch("metaswitch.crest.api.homestead.cassandra.CassandraClient")
        self.CassandraClient = patcher.start()
        self.addCleanup(patcher.stop)

        self.cass_client = mock.MagicMock()
        self.CassandraClient.return_value = self.cass_client

        CacheModel.start_connection()
        self.cache = Cache()

    def test_put_digest(self):
        self.cass_client.batch_insert.return_value = batch_insert = defer.Deferred()
        res = Result(self.cache.put_digest("priv", "digest"))
        self.cass_client.batch_insert.assert_called_once_with(
                                               key="priv",
                                               column_family="impi",
                                               mapping={"digest_ha1": "digest"},
                                               ttl=None)
        batch_insert.callback(None)
        self.assertEquals(res.value(), None)


    def test_put_associated_public_id(self):
        self.cass_client.batch_insert.return_value = batch_insert = defer.Deferred()
        res = Result(self.cache.put_associated_public_id("priv", "kermit"))
        self.cass_client.batch_insert.assert_called_once_with(
                                             key="priv",
                                             column_family="impi",
                                             mapping={"public_id_kermit": None},
                                             ttl=None)
        batch_insert.callback(None)
        self.assertEquals(res.value(), None)

    def test_put_ims_subscription(self):
        self.cass_client.batch_insert.return_value = batch_insert = defer.Deferred()
        res = Result(self.cache.put_ims_subscription("pub", "xml"))
        self.cass_client.batch_insert.assert_called_once_with(
                                        key="pub",
                                        column_family="impu",
                                        mapping={"ims_subscription_xml": "xml"},
                                        ttl=None)
        batch_insert.callback(None)
        self.assertEquals(res.value(), None)

    def test_get_ims_subscription(self):
        self.cass_client.get_slice.return_value = get_slice = defer.Deferred()
        res = Result(self.cache.get_ims_subscription("pub"))

        self.cass_client.get_slice.assert_called_once_with(
                                                 key="pub",
                                                 column_family="impu",
                                                 names=["ims_subscription_xml"])
        get_slice.callback([MockColumn("ims_subscription_xml", "xml")])
        self.assertEquals(res.value(), "xml")

    def test_get_digest_no_pub_id_supp(self):
        self.cass_client.get_slice.return_value = get_slice = defer.Deferred()
        res = Result(self.cache.get_digest("priv"))

        self.cass_client.get_slice.assert_called_once_with(
                                                 key="priv",
                                                 column_family="impi",
                                                 names=["digest_ha1"])
        get_slice.callback([MockColumn("digest_ha1", "digest")])
        self.assertEquals(res.value(), "digest")

    def test_get_digest_no_pub_id_assoc(self):
        self.cass_client.get_slice.return_value = get_slice = defer.Deferred()
        res = Result(self.cache.get_digest("priv", "miss_piggy"))

        self.cass_client.get_slice.assert_called_once_with(
                                   key="priv",
                                   column_family="impi",
                                   names=["digest_ha1", "public_id_miss_piggy"])
        get_slice.callback([MockColumn("digest_ha1", "digest"),
                            MockColumn("public_id_kermit", None)])
        self.assertEquals(res.value(), None)

    def test_get_digest_right_pub_id(self):
        self.cass_client.get_slice.return_value = get_slice = defer.Deferred()
        res = Result(self.cache.get_digest("priv", "miss_piggy"))

        self.cass_client.get_slice.assert_called_once_with(
                                   key="priv",
                                   column_family="impi",
                                   names=["digest_ha1", "public_id_miss_piggy"])
        get_slice.callback([MockColumn("digest_ha1", "digest"),
                            MockColumn("public_id_miss_piggy", None)])
        self.assertEquals(res.value(), "digest")
