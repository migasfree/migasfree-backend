# -*- coding: utf-8 -*-

# Copyright (c) 2015-2018 Jose Antonio Chavarría <jachavar@gmail.com>
# Copyright (c) 2015-2018 Alberto Gacías <alberto@migasfree.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import random
import string


def secret_key(path):
    if not os.path.exists(path):
        os.makedirs(path)

    _file = os.path.join(path, 'secret_key.txt')
    if os.path.exists(_file):
        key = open(_file).read().strip()
    else:
        key = ''.join([random.SystemRandom().choice("%s%s%s" % (
            string.ascii_letters,
            string.digits,
            string.punctuation
        )) for i in range(50)])

        with open(_file, 'w') as outfile:
            outfile.write(key)

    return key
