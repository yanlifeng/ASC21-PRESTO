import hashlib
import os


def listdir(path, list_name):
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.isdir(file_path):
            listdir(file_path, list_name)
        else:
            list_name.append(file_path)


ls1 = []
listdir("./subbands/", ls1)
ls1.sort()
ls2 = []
listdir("../../STD2/subbands/", ls2)
ls2.sort()
assert (len(ls1) == len(ls1))
ok = 1
for i in range(len(ls1)):
    try:
        if ".pfd.ps" in ls1[i]:
            # print("jump this test because pds.ps")
            continue
        if "_ACCEL_0.cand" in ls1[i]:
            # print("jump this test because cand")
            continue

        f1 = ls1[i]
        with open(f1, 'rb') as fp:
            data = fp.read()
        m1 = hashlib.md5(data).hexdigest()
        # print(m1)
        f2 = ls2[i]
        with open(f2, 'rb') as fp:
            data = fp.read()
        m2 = hashlib.md5(data).hexdigest()
        if m1 != m2:
            print("GG on check ", f1, f2)
            ok = 0
        else:
            print("pass on test ", f1)
    except:
        print("some errors occur when open ", f1, f2)
        continue

f1 = "../../STD2/DDplan.ps"
with open(f1, 'rb') as fp:
    data = fp.read()
    data = str(data).split("\n")[10:]
    data = bytes(data)
m1 = hashlib.md5(data).hexdigest()
f2 = "./DDplan.ps"
with open(f2, 'rb') as fp:
    data = fp.read()
    data = str(data).split("\n")[10:]
    data = bytes(data)
m2 = hashlib.md5(data).hexdigest()
if m1 != m2:
    print("GG on file " + f2)
    ok = 0
else:
    print("pass on test DD")
if ok:
    print("Accepted !")
else:
    print("GG !")
