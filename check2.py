#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import hashlib

if __name__ == '__main__':
    # TODO _ACCEL_0.cand文件的check还有一点问题，单线程也有问题，可以详细看看后面的代码。
    # name = ["_ACCEL_0", "_ACCEL_0.cand", "_ACCEL_0.txtcand", ".dat", ".fft", ".inf"]
    name = ["_ACCEL_0", "_ACCEL_0.txtcand", ".dat", ".fft", ".inf"]
    ok = 1
    path1 = "../../STD2/subbands/"
    path2 = "./subbands/"
    Tt = [".00", ".20", ".40", ".60", ".80"]

    for id in range(200):
        testOk = 1
        for tt in Tt:
            for it in name:
                try:
                    f1 = path1 + "Sband_DM" + str(id) + tt + it
                    with open(f1, 'rb') as fp:
                        data = fp.read()
                    m1 = hashlib.md5(data).hexdigest()
                    # print(m1)
                    f2 = path2 + "Sband_DM" + str(id) + tt + it
                    with open(f2, 'rb') as fp:
                        data = fp.read()
                    m2 = hashlib.md5(data).hexdigest()
                    # print(m2)
                    # print(f1)
                    # print(f2)
                    if m1 != m2:
                        print(it + " GG !!")
                        testOk = 0
                except:
                    print("some errors occur when open ", id)
                    testOk = 0
                    break
            # print "================================================="
        if testOk == 0:
            print("GG on test " + str(id))
            ok = 0
            break
        else:
            print("pass on test " + str(id))

    f1 = "../../STD2/DDplan.ps"
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

    logList = ["accelsearch", "dedisperse", "fft", "folding"]
    for it in logList:
        f1 = path1 + it + ".log"
        with open(f1, 'rb') as fp:
            data = fp.read()
        m1 = hashlib.md5(data).hexdigest()
        # print(m1)
        f2 = path2 + it + ".log"
        with open(f2, 'rb') as fp:
            data = fp.read()
        m2 = hashlib.md5(data).hexdigest()
        # print(m2)
        # print(f1)
        # print(f2)
        if m1 != m2:
            print(it + " test GG")
        else:
            print(it + " test pass")
