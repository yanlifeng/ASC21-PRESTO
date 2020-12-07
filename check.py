#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import hashlib

if __name__ == '__main__':
    ok = 1
    for id in range(200):
        try:
            f1 = "../../STD/1TestData/subbands/Sband_DM" + str(id) + ".00.dat"
            with open(f1, 'rb') as fp:
                data = fp.read()
            m1 = hashlib.md5(data).hexdigest()
            # print(m1)
            f2 = "subbands/Sband_DM" + str(id) + ".00.dat"
            with open(f2, 'rb') as fp:
                data = fp.read()
            m2 = hashlib.md5(data).hexdigest()
            # print(m2)
            if m1 != m2:
                print("GG on file " + f2)
                ok = 0
            f1 = "../../STD/1TestData/subbands/Sband_DM" + str(id) + ".50.dat"
            with open(f1, 'rb') as fp:
                data = fp.read()
            m1 = hashlib.md5(data).hexdigest()
            # print(m1)
            f2 = "subbands/Sband_DM" + str(id) + ".50.dat"
            with open(f2, 'rb') as fp:
                data = fp.read()
            m2 = hashlib.md5(data).hexdigest()
            # print(m2)
            if m1 != m2:
                print("GG on file " + f2)
                ok = 0
            # print "================================================="
            print("pass on test " + str(id))
        except:

            continue
    if ok == 1:
        print("Accepted!")
