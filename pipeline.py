# coding=utf-8
"""
A simple pipelien for demostrating presto
Weiwei Zhu
2015-08-14
Max-Plank Institute for Radio Astronomy
zhuwwpku@gmail.com
"""

import os, sys, glob, re
import threading

import presto.sifting as sifting
from subprocess import getoutput
import numpy as np
import time
import random
from operator import itemgetter, attrgetter


class TestThread(threading.Thread):
    def __init__(self, func, args=()):
        super(TestThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result  # 如果子线程不使用join方法，此处可能会报没有self.result的错误
        except Exception:
            return None


def dur(op=None, clock=[time.time()]):
    res = ''
    if op != None:
        duration = time.time() - clock[0]
        res = '%-30s === %.6f \n' % (op, duration)
    clock[0] = time.time()
    return res


def fft_and_acc(fftcmd, searchcmd):
    sm.acquire()
    # print("fft_and_acc")
    # print(fftcmd)
    # print(searchcmd)
    # print()
    r1 = getoutput(fftcmd)
    r2 = getoutput(searchcmd)
    sm.release()
    return r1, r2


def fft_and_accp(fftcmd, searchcmd):
    r1 = getoutput(fftcmd)
    r2 = getoutput(searchcmd)
    return r1, r2


def prep(l, r, prepcmd1, prepcmd2):
    sm.acquire()
    # print("prep")
    # print(prepcmd1)
    # print(prepcmd2)
    # print()
    r1 = getoutput(prepcmd1)
    r2 = getoutput(prepcmd2)
    for i in range(l, r):
        hasDone[i] = 1
    sm.release()
    return r1, r2


def prepp(prepcmd1, prepcmd2):
    r1 = getoutput(prepcmd1)
    r2 = getoutput(prepcmd2)

    return r1, r2


def foldcmdFunc(i, cand):
    sm.acquire()
    # foldcmd = "prepfold -dm %(dm)f -accelcand %(candnum)d -accelfile %(accelfile)s %(datfile)s -noxwin " % {
    # 'dm':cand.DM,  'accelfile':cand.filename+'.cand', 'candnum':cand.candnum, 'datfile':('%s_DM%s.dat' % (rootname, cand.DMstr))} #simple plots
    foldcmd = "prepfold -ncpus %(Cthread4)d -n %(Nint)d -nsub %(Nsub)d -dm %(dm)f -p %(period)f %(filfile)s -o %(outfile)s -noxwin -nodmsearch" % {
        'Cthread4': Cthread4, 'Nint': Nint, 'Nsub': Nsub, 'dm': cand.DM, 'period': cand.p, 'filfile': filename,
        'outfile': rootname + '_DM' + cand.DMstr}  # full plots
    print(foldcmd)
    # os.system(foldcmd)
    output = getoutput(foldcmd)
    sm.release()
    return output


# Tutorial_Mode = True
Tutorial_Mode = False

timeLog = ''

rootname = 'Sband'
maxDM = 80  # max DM to search
Nsub = 32  # 32 subbands
Nint = 64  # 64 sub integration
Tres = 0.5  # ms
zmax = 0

hasDone = [0 for _ in range(1000)]

CThreadNumber = 1
Cthread1 = CThreadNumber
Cthread2 = CThreadNumber
Cthread3 = CThreadNumber
Cthread4 = CThreadNumber

maxThreadNumber = 8
threadController = int(sys.argv[2])
if threadController == 1:
    sm = threading.Semaphore(maxThreadNumber)

print("threadController %d\n" % threadController)

filename = sys.argv[1]
if len(sys.argv) > 3:
    maskfile = sys.argv[3]
else:
    maskfile = None


def query(question, answer, input_type):
    print("Based on output of the last step, answer the following questions:")
    Ntry = 3
    while not input_type(input("%s:" % question)) == answer and Ntry > 0:
        Ntry -= 1
        print("try again...")
    if Ntry == 0: print("The correct answer is:", answer)


def cc(cmd):
    return getoutput(cmd)


# """

print('''
====================Read Header======================
''')
# read some canshu from filename
# 算了 中文注释吧
# 读取文件的信息 一些参数
dur()
# try:
# myfil = filterbank(filename)

readheadercmd = 'readfile %s' % filename
print("readheadercmd : \n" + readheadercmd)
output = getoutput(readheadercmd)
print("output : \n" + output)
header = {}
size = 0
for line in output.split('\n'):
    size += 1
    items = line.split("=")
    if len(items) > 1:
        header[items[0].strip()] = items[1].strip()
# print header
# except:
# print 'failed at reading file %s.' % filename
# sys.exit(0)
timeLog += dur("Read Header")

print('''
============Generate Dedispersion===============
''')
dur()
try:
    Nchan = int(header['Number of channels'])
    tsamp = float(header['Sample time (us)']) * 1.e-6
    BandWidth = float(header['Total Bandwidth (MHz)'])
    fcenter = float(header['Central freq (MHz)'])
    Nsamp = int(header['Spectra per file'])

    if Tutorial_Mode:
        query("Input file has how many frequency channel?", Nchan, int)
        query("what is the total bandwidth?", BandWidth, float)
        query("what is the size of each time sample in us?", tsamp * 1.e6, float)
        query("what's the center frequency?", fcenter, float)
        print('see how these numbers are used in the next step.')
        print('')
    # 利用读取出来的参数 运行DDplan.py 然后收集到输出中的最后一行参数
    ddplancmd = 'DDplan.py -d %(maxDM)s -n %(Nchan)d -b %(BandWidth)s -t %(tsamp)f -f %(fcenter)f -s %(Nsub)s -o DDplan.ps' % {
        'maxDM': maxDM, 'Nchan': Nchan, 'tsamp': tsamp, 'BandWidth': BandWidth, 'fcenter': fcenter, 'Nsub': Nsub}
    print(ddplancmd)
    ddplanout = getoutput(ddplancmd)
    print(ddplanout)
    planlist = ddplanout.split('\n')
    ddplan = []
    planlist.reverse()
    for plan in planlist:
        if plan == '':
            continue
        elif plan.strip().startswith('Low DM'):
            break
        else:
            ddplan.append(plan)
    ddplan.reverse()
    # ddplan is ['    0.000     84.000    0.50       1   12.00     168      24       7    1']
    # print "ddplan : \n"
    # print ddplan
except:
    print('failed at generating DDplan.')
    sys.exit(0)

if Tutorial_Mode:
    calls = 0
    for line in ddplan:
        ddpl = line.split()
        calls += int(ddpl[7])
    query("According to the DDplan, how many times in total do we have to call prepsubband?", calls, int)
    print('see how these numbers are used in the next step.')
    print('')
timeLog += dur("Generate Dedispersion")

print('''
================Dedisperse Subbands==================
''')
dur()
cwd = os.getcwd()
try:
    task_prep = []
    task_fft_and_acc = []
    if not os.access('subbands', os.F_OK):
        os.mkdir('subbands')
    os.chdir('subbands')
    logfile = open('dedisperse.log', 'wt')
    logfileFFT = open('fft.log', 'wt')
    logfileACC = open('accelsearch.log', 'wt')
    ddplanSize = 0
    # 对于DDplan的输出信息们（其实就一行） 生成一个lowDM-highDM 间隔为dDm的数组 分成calls份
    # 然后每一份 运行prepsubband 先写一些信息到临时文件里 然后读出来 把有用的信息写到Sband_DMxx.xx里面
    # 最后删掉临时文件 并把log信息存在 dedisperse.log 里面
    for line in ddplan:
        # print "ddplanSize : "
        # print ddplanSize
        ddplanSize += 1
        ddpl = line.split()
        lowDM = float(ddpl[0])
        hiDM = float(ddpl[1])
        dDM = float(ddpl[2])
        DownSamp = int(ddpl[3])
        NDMs = int(ddpl[6])
        calls = int(ddpl[7])
        Nout = Nsamp / DownSamp
        Nout -= (Nout % 500)
        dmlist = np.split(np.arange(lowDM, hiDM, dDM), calls)

        preDm = NDMs
        print("preDm : ")
        print(preDm)
        # print "dmlist : "
        # print dmlist
        # copy from $PRESTO/python/Dedisp.py
        subdownsamp = DownSamp / 2
        datdownsamp = 2
        if DownSamp < 2: subdownsamp = datdownsamp = 1

        # random.shuffle(dmlist)
        for i, dml in enumerate(dmlist):
            lodm = dml[0]
            subDM = np.mean(dml)

            if maskfile:
        # print "maskfile has open"
                prepsubband = "prepsubband -ncpus %d -sub -subdm %.2f -nsub %d -downsamp %d -mask ../%s -o %s %s" % (
                    Cthread1, subDM, Nsub, subdownsamp, maskfile, rootname, '../' + filename)
            else:
                prepsubband = "prepsubband -ncpus %d -sub -subdm %.2f -nsub %d -downsamp %d -o %s %s" % (
                    Cthread1, subDM, Nsub, subdownsamp, rootname, '../' + filename)
            # print("prepsubband : " + prepsubband)

            # print output
            # print "========================================================================"
            subnames = rootname + "_DM%.2f.sub[0-9]*" % subDM
            # prepsubcmd = "prepsubband -nsub %(Nsub)d -lodm %(lowdm)f -dmstep %(dDM)f -numdms %(NDMs)d -numout %(Nout)d -downsamp %(DownSamp)d -o %(root)s ../%(filfile)s" % {
            # 'Nsub':Nsub, 'lowdm':lodm, 'dDM':dDM, 'NDMs':NDMs, 'Nout':Nout, 'DownSamp':datdownsamp, 'root':rootname, 'filfile':filename}
            prepsubcmd = "prepsubband -ncpus %(Cthread1)d -nsub %(Nsub)d -lodm %(lowdm)f -dmstep %(dDM)f -numdms %(NDMs)d -numout %(Nout)d -downsamp %(DownSamp)d -o %(root)s %(subfile)s" % {
                'Cthread1': Cthread1, 'Nsub': Nsub, 'lowdm': lodm, 'dDM': dDM, 'NDMs': NDMs, 'Nout': Nout,
                'DownSamp': datdownsamp, 'root': rootname, 'subfile': subnames}
            # print("prepsubcmd : " + prepsubcmd)
            task_prep.append([prepsubband, prepsubcmd])
            for idx in dml:
                df = "Sband_DM%.2f" % idx + ".dat"
                fftcmd = "realfft %s" % df
                # print(fftcmd)
                df = "Sband_DM%.2f" % idx + ".fft"
                searchcmd = "accelsearch -ncpus %d -zmax %d %s" % (Cthread3, zmax, df)                # print(searchcmd)
                task_fft_and_acc.append([fftcmd, searchcmd])

            # print output
            # print "========================================================================"

        if threadController == 1:
            threads = []
            falgs = []
            sub_f1 = prep
            sub_f2 = fft_and_acc
            for i, it in enumerate(task_prep):
                t = TestThread(sub_f1, args=(i * preDm, (i + 1) * preDm, it[0], it[1]))
                threads.append(t)
                falgs.append(0)
                t.start()
            time.sleep(1)
            tarTask = len(task_fft_and_acc)
            doneTaskNumber = 0
            las = [i for i in range(tarTask)]
            while doneTaskNumber < tarTask:
                nowlas = []
                for id in las:
                    if hasDone[id] == 0:
                        nowlas.append(id)
                        continue
                    # print("%d start fft_acc" % id)
                    it = task_fft_and_acc[id]
                    t = TestThread(sub_f2, args=(it[0], it[1]))
                    threads.append(t)
                    falgs.append(1)
                    doneTaskNumber += 1
                    t.start()
                las = nowlas
                time.sleep(0.1)
            # for i, it in enumerate(task_fft_and_acc):
            #     while hasDone[i] == 0:
            #         print("producer is working, %d pending..." % i)
            #         time.sleep(0.5)
            #     t = TestThread(sub_f2, args=(i, it[0], it[1]))
            #     threads.append(t)
            #     falgs.append(1)
            #     t.start()
            for i, t in enumerate(threads):
                t.join()
                r1, r2 = t.get_result()
                if falgs[i] == 0:
                    logfile.write(r1)
                    logfile.write(r2)
                else:
                    logfileFFT.write(r1)
                    logfileACC.write(r2)
        else:
            for i, it in enumerate(task_prep):
                r1, r2 = prepp(it[0], it[1])
                logfile.write(r1)
                logfile.write(r2)

            for i, it in enumerate(task_fft_and_acc):
                r1, r2 = fft_and_accp(it[0], it[1])
                logfileFFT.write(r1)
                logfileACC.write(r2)

    os.system('rm *.sub*')
    logfile.close()
    logfileFFT.close()
    logfileACC.close()
    os.chdir(cwd)

except:
    print('failed at prepsubband.')
    os.chdir(cwd)
    sys.exit(0)
timeLog += dur("Dedisperse Subbands")


# exit(0)
#
# print('''
# ================fft-search subbands==================
# ''')
# dur()
# try:
#     os.chdir('subbands')
#     datfiles = glob.glob("*.dat")
#     logfileFFT = open('fft.log', 'wt')
#     logfileACC = open('accelsearch.log', 'wt')
#
#     for df in datfiles:
#         fftcmd = "realfft %s" % df
#         print(fftcmd)
#         output = getoutput(fftcmd)
#         logfileFFT.write(output)
#         df = df.replace("dat", "fft")
#         searchcmd = "accelsearch -zmax %d %s" % (zmax, df)
#         print(searchcmd)
#         output = getoutput(searchcmd)
#         logfileACC.write(output)
#     logfileFFT.close()
#     logfileACC.close()
#
#     # logfile = open('accelsearch.log', 'wt')
#     # fftfiles = glob.glob("*.fft")
#     # for fftf in fftfiles:
#     #     searchcmd = "accelsearch -zmax %d %s" % (zmax, fftf)
#     #     print(searchcmd)
#     #     output = getoutput(searchcmd)
#     #     logfile.write(output)
#     # logfile.close()
#     os.chdir(cwd)
# except:
#     print('failed at fft search.')
#     os.chdir(cwd)
#     sys.exit(0)
#
# timeLog += dur("fft-search subbands")
#

# """


def ACCEL_sift(zmax):
    '''
    The following code come from PRESTO's ACCEL_sift.py
    '''

    globaccel = "*ACCEL_%d" % zmax
    globinf = "*DM*.inf"
    # In how many DMs must a candidate be detected to be considered "good"
    min_num_DMs = 2
    # Lowest DM to consider as a "real" pulsar
    low_DM_cutoff = 2.0
    # Ignore candidates with a sigma (from incoherent power summation) less than this
    sifting.sigma_threshold = 4.0
    # Ignore candidates with a coherent power less than this
    sifting.c_pow_threshold = 100.0

    # If the birds file works well, the following shouldn't
    # be needed at all...  If they are, add tuples with the bad
    # values and their errors.
    #                (ms, err)
    sifting.known_birds_p = []
    #                (Hz, err)
    sifting.known_birds_f = []

    # The following are all defined in the sifting module.
    # But if we want to override them, uncomment and do it here.
    # You shouldn't need to adjust them for most searches, though.

    # How close a candidate has to be to another candidate to                
    # consider it the same candidate (in Fourier bins)
    sifting.r_err = 1.1
    # Shortest period candidates to consider (s)
    sifting.short_period = 0.0005
    # Longest period candidates to consider (s)
    sifting.long_period = 15.0
    # Ignore any candidates where at least one harmonic does exceed this power
    sifting.harm_pow_cutoff = 8.0

    # --------------------------------------------------------------

    # Try to read the .inf files first, as _if_ they are present, all of
    # them should be there.  (if no candidates are found by accelsearch
    # we get no ACCEL files...
    inffiles = glob.glob(globinf)
    candfiles = glob.glob(globaccel)
    # Check to see if this is from a short search
    if len(re.findall("_[0-9][0-9][0-9]M_", inffiles[0])):
        dmstrs = [x.split("DM")[-1].split("_")[0] for x in candfiles]
    else:
        dmstrs = [x.split("DM")[-1].split(".inf")[0] for x in inffiles]
    dms = list(map(float, dmstrs))
    dms.sort()
    dmstrs = ["%.2f" % x for x in dms]

    # Read in all the candidates
    cands = sifting.read_candidates(candfiles)

    # Remove candidates that are duplicated in other ACCEL files
    if len(cands):
        cands = sifting.remove_duplicate_candidates(cands)

    # Remove candidates with DM problems
    if len(cands):
        cands = sifting.remove_DM_problems(cands, min_num_DMs, dmstrs, low_DM_cutoff)

    # Remove candidates that are harmonically related to each other
    # Note:  this includes only a small set of harmonics
    if len(cands):
        cands = sifting.remove_harmonics(cands)

    # Write candidates to STDOUT
    if len(cands):
        cands.sort(key=attrgetter('sigma'), reverse=True)
        # cands.sort(sifting.cmp_sigma)
        # for cand in cands[:1]:
        # print cand.filename, cand.candnum, cand.p, cand.DMstr
        # sifting.write_candlist(cands)
    return cands


print('''
================sifting candidates==================
''')
dur()
# try:
cwd = os.getcwd()
os.chdir('subbands')
cands = ACCEL_sift(zmax)
os.chdir(cwd)
# except:
# print 'failed at sifting candidates.'
# os.chdir(cwd)
# sys.exit(0)

timeLog += dur("sifting candidates")
print('''
================folding candidates==================
''')
dur()
try:
    cwd = os.getcwd()
    os.chdir('subbands')
    os.system('ln -s ../%s %s' % (filename, filename))
    logfile = open('folding.log', 'wt')
    if threadController == 1:
        sub_f = foldcmdFunc
        threads = []
        for i, cand in enumerate(cands):
            t = TestThread(sub_f, args=(i, cand))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
            logfile.write(t.get_result())
    else:
        for cand in cands:
            # foldcmd = "prepfold -dm %(dm)f -accelcand %(candnum)d -accelfile %(accelfile)s %(datfile)s -noxwin " % {
            # 'dm':cand.DM,  'accelfile':cand.filename+'.cand', 'candnum':cand.candnum, 'datfile':('%s_DM%s.dat' % (rootname, cand.DMstr))} #simple plots
            foldcmd = "prepfold -ncpus %(Cthread4)d -n %(Nint)d -nsub %(Nsub)d -dm %(dm)f -p %(period)f %(filfile)s -o %(outfile)s -noxwin -nodmsearch" % {
                'Cthread4': Cthread4, 'Nint': Nint, 'Nsub': Nsub, 'dm': cand.DM, 'period': cand.p, 'filfile': filename,
                'outfile': rootname + '_DM' + cand.DMstr}  # full plots
            print(foldcmd)
            # os.system(foldcmd)
            output = getoutput(foldcmd)
            logfile.write(output)
    logfile.close()
    os.chdir(cwd)
except:
    print('failed at folding candidates.')
    os.chdir(cwd)
    sys.exit(0)
timeLog += dur("folding candidates")

print(timeLog)
