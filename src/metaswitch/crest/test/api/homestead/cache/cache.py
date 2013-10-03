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

import mock
import unittest

from twisted.internet import defer

from metaswitch.crest.api.homestead.cache.cache import Cache
from metaswitch.crest.api.homestead.cache.db import CacheModel
from metaswitch.crest.test.matchers import DictContaining, ListContaining

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

        # Dummy timestamp used for cache puts.
        self.timestamp = 1234

    def test_put_digest(self):
        """Test a digest can be put into the cache"""

        self.cass_client.batch_insert.return_value = batch_insert = defer.Deferred()
        res = Result(self.cache.put_digest("priv", "digest", self.timestamp))
        self.cass_client.batch_insert.assert_called_once_with(
                                               key="priv",
                                               column_family="impi",
                                               mapping=DictContaining({"digest_ha1": "digest"}),
                                               ttl=None,
                                               timestamp=self.timestamp)
        batch_insert.callback(None)
        self.assertEquals(res.value(), None)


    def test_put_associated_public_id(self):
        """Test a public ID associated with the private ID can be put into the
        cache"""

        self.cass_client.batch_insert.return_value = batch_insert = defer.Deferred()
        res = Result(self.cache.put_associated_public_id("priv",
                                                         "kermit",
                                                         self.timestamp))
        self.cass_client.batch_insert.assert_called_once_with(
                                             key="priv",
                                             column_family="impi",
                                             mapping=DictContaining({"public_id_kermit": ""}),
                                             ttl=None,
                                             timestamp=self.timestamp)
        batch_insert.callback(None)
        self.assertEquals(res.value(), None)

    def test_put_ims_subscription(self):
        """Test an IMS subscription can be put into the cache"""
        self.cass_client.batch_insert.return_value = batch_insert = defer.Deferred()
        res = Result(self.cache.put_ims_subscription("pub",
                                                     "xml",
                                                     self.timestamp))
        self.cass_client.batch_insert.assert_called_once_with(
                                        key="pub",
                                        column_family="impu",
                                        mapping=DictContaining({"ims_subscription_xml": "xml"}),
                                        ttl=None,
                                        timestamp=self.timestamp)
        batch_insert.callback(None)
        self.assertEquals(res.value(), None)

    def test_get_ims_subscription(self):
        """Test an IMS subscription can be fetched from the cache"""

        self.cass_client.get_slice.return_value = get_slice = defer.Deferred()
        res = Result(self.cache.get_ims_subscription("pub"))

        self.cass_client.get_slice.assert_called_once_with(
                                                 key="pub",
                                                 column_family="impu",
                                                 names=ListContaining(["ims_subscription_xml"]))
        get_slice.callback([MockColumn("ims_subscription_xml", "xml"),
                            MockColumn("_exists", "")])
        self.assertEquals(res.value(), "xml")

    def test_get_digest_no_pub_id_supp(self):
        """Test a digest can be got from the cache when no public ID is
        supplied"""

        self.cass_client.get_slice.return_value = get_slice = defer.Deferred()
        res = Result(self.cache.get_digest("priv"))

        self.cass_client.get_slice.assert_called_once_with(
                                                 key="priv",
                                                 column_family="impi",
                                                 names=ListContaining(["digest_ha1"]))
        get_slice.callback([MockColumn("digest_ha1", "digest"),
                            MockColumn("_exists", "")])
        self.assertEquals(res.value(), "digest")

    def test_get_digest_no_pub_id_assoc(self):
        """Test that is you specify a required public ID when getting a digest,
        that nothing is returned if that ID is not associated with the private
        ID."""

        self.cass_client.get_slice.return_value = get_slice = defer.Deferred()
        res = Result(self.cache.get_digest("priv", "miss_piggy"))

        self.cass_client.get_slice.assert_called_once_with(
                                   key="priv",
                                   column_family="impi",
                                   names=ListContaining(["digest_ha1", "public_id_miss_piggy"]))
        get_slice.callback([MockColumn("digest_ha1", "digest"),
                            MockColumn("public_id_kermit", None),
                            MockColumn("_exists", "")])
        self.assertEquals(res.value(), None)

    def test_get_digest_right_pub_id(self):
        """Test that is you specify a required public ID when getting a digest,
        that the digest IS returned if that ID IS associated with the private
        ID."""

        self.cass_client.get_slice.return_value = get_slice = defer.Deferred()
        res = Result(self.cache.get_digest("priv", "miss_piggy"))

        self.cass_client.get_slice.assert_called_once_with(
                                   key="priv",
                                   column_family="impi",
                                   names=ListContaining(["digest_ha1", "public_id_miss_piggy"]))
        get_slice.callback([MockColumn("digest_ha1", "digest"),
                            MockColumn("public_id_miss_piggy", None),
                            MockColumn("_exists", "")])
        self.assertEquals(res.value(), "digest")
