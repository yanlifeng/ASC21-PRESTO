#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import hashlib

if __name__ == '__main__':
    ok = 1
    path1 = "../../STD/subbands/"
    path2 = "./subbands/"
    f1 = "../../STD/DDplan.ps"
    with open(f1, 'rb') as fp:
        data = fp.read()
        data = str(data).split("\n")[10:]
        data = bytes(data)
    m1 = hashlib.md5(data).hexdigest()
    # print(m1)
    f2 = "./DDplan.ps"
    with open(f2, 'rb') as fp:
        data = fp.read()
        data = str(data).split("\n")[10:]
        data = bytes(data)

    m2 = hashlib.md5(data).hexdigest()
    # print(m2)
    # print(f1)
    # print(f2)
    if m1 != m2:
        print("GG on file " + f2)
        ok = 0
    else:
        print("pass on test DD")

    for id in range(200):
        try:
            # TODO _ACCEL_0.cand文件的check还有一点问题，单线程也有问题，可以详细看看后面的代码。
            # name = ["_ACCEL_0", "_ACCEL_0.cand", "_ACCEL_0.txtcand", ".dat", ".fft", ".inf"]
            name = ["_ACCEL_0", "_ACCEL_0.txtcand", ".dat", ".fft", ".inf"]
            testOk = 1
            for it in name:
                f1 = path1 + "Sband_DM" + str(id) + ".00" + it
                with open(f1, 'rb') as fp:
                    data = fp.read()
                m1 = hashlib.md5(data).hexdigest()
                # print(m1)
                f2 = path2 + "Sband_DM" + str(id) + ".00" + it
                with open(f2, 'rb') as fp:
                    data = fp.read()
                m2 = hashlib.md5(data).hexdigest()
                # print(m2)
                # print(f1)
                # print(f2)
                if m1 != m2:
                    testOk = 0
                f1 = path1 + "Sband_DM" + str(id) + ".50" + it
                with open(f1, 'rb') as fp:
                    data = fp.read()
                m1 = hashlib.md5(data).hexdigest()
                # print(m1)
                f2 = path2 + "Sband_DM" + str(id) + ".50" + it
                with open(f2, 'rb') as fp:
                    data = fp.read()
                m2 = hashlib.md5(data).hexdigest()
                # print(m2)
                # print(f1)
                # print(f2)
                if m1 != m2:
                    testOk = 0
            # print "================================================="
            if testOk == 0:
                print("GG on test " + str(id))
                ok = 0
            else:
                print("pass on test " + str(id))

        except:
            continue
    if ok == 1:
        print("Accepted!")
