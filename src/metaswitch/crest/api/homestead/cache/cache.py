# @file handlers.py
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

import logging

from twisted.internet import defer
from .db import IMPI, IMPU

_log = logging.getLogger("crest.api.homestead.cache")


class Cache(object):

    @defer.inlineCallbacks
    def get_digest(self, private_id, public_id=None):
        digest_ha1 = yield IMPI(private_id).get_digest_ha1(public_id)
        defer.returnValue(digest_ha1)

    @defer.inlineCallbacks
    def get_ims_subscription(self, public_id, private_id=None):
        xml = yield IMPU(public_id).get_ims_subscription()
        defer.returnValue(xml)

    @defer.inlineCallbacks
    def put_digest(self, private_id, digest, timestamp):
        yield IMPI(private_id).put_digest_ha1(digest, timestamp)

    @defer.inlineCallbacks
    def put_associated_public_id(self, private_id, public_id, timestamp):
        yield IMPI(private_id).put_associated_public_id(public_id, timestamp)

    @defer.inlineCallbacks
    def put_ims_subscription(self, public_id, xml, timestamp):
        yield IMPU(public_id).put_ims_subscription(xml, timestamp)

    @defer.inlineCallbacks
    def delete_private_id(self, private_id):
        yield IMPI(private_id).delete()

    @defer.inlineCallbacks
    def delete_public_id(self, public_id):
        yield IMPU(public_id).delete()

