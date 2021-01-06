# PRESTO
TODO

（截止到目前）

- [x] 编译器换成icc
- [x] fortan换成intel的
- [x] 完成环境配置
- [x] 初步寻找热点
- [x] 做好check
- [x] 测试get_num_threads
- [x] 修改编译参数
- [x] 解决python tests的报错
- [ ] 解决prepsubband运行的error
- [x] 尝试python脚本级别的并行
- [ ] 解决CPU使用率低的问题
- [x] 解决只能检测到一个线程的问题
- [x] 解决_ACCEL_0.cand文件check出错的问题
- [x] 输出log，并做check
- [ ] 解决上次输出没有清空的时候运行变慢（maybe）
- [x] ~~把prepsubb里面的两个脚本拆开~~
- [x] 规定python线程库的threadNumber测试加速比
- [x] 关于第1，3个热点加速比一般的原因
- [x] check pfd!!
- [x] 去内部的.c文件并行
- [x] 更换简洁的check方法
- [ ] 去6148上用root配一下环境
- [ ] 去ylff上用非root配一下环境
- [x] 解决-mavx2 folding.log和pfd报错的问题
- [ ] 研究一下amoeba为啥那么慢
- [x] 解决fold中没有权限的问题
- [ ] fftw换成mkl的
- [ ] 解决icc和gcc答案不一样
- [ ] 解决Ofast ffast-math
- [ ] 
- [ ] 
- [ ] 
- [ ] 

## 1116-1119

摸鱼+配环境
asc要了个root权限，配好之后换成了preto2.2
然后asc连接开始不稳定，日常连不上
然后直接在PC上弄了弄环境，想用mac ssh PC
租了个服务器做跳转机
## 1120
不能摸了，抓紧干活
初始程序跑一跑，打个timer

#### workload1

```bash
Read Header                    === 0.003682 
Generate Dedispersion          === 0.080350 
Dedisperse Subbands            === 8.240596 
fft-search subbands            === 35.706232 
sifting candidates             === 0.098624 
folding candidates             === 21.515613 


real	1m5.973s
user	1m12.852s
sys	0m18.308s
```
#### workload2
```c+++
Read Header                    === 0.003768 
Generate Dedispersion          === 0.090177 
Dedisperse Subbands            === 66.568033 
fft-search subbands            === 135.115792 
sifting candidates             === 0.549006 
folding candidates             === 157.755927 


real	6m0.366s
user	6m23.564s
sys	0m57.216s
```

### 1206

摸了好久了

重新加好了计时函数，在asc上重测了上面的时间

对于Dedisperse Subbands的过程，准备加多线程，先编写了check程序，以及STD标准答案

### 1207

开始对Dedisperse Subbands上多线程了

大概的热点是运行prepsubband，workload1是运行了7次，其实不太好并行，一方面是不知道他们内部是否存在写冲突（shuffle了一下，一来应该是不存在的）另一方面是7个任务，线程多的时候不合适，所以先找到prepsubband的源代码读一读吧。

考虑了一下还是决定用3.0，怕2.2有什么bug啥的。

```c

    if (cmd->ncpus > 1) {
#ifdef _OPENMP
        int maxcpus = omp_get_num_procs();
        int openmp_numthreads = (cmd->ncpus <= maxcpus) ? cmd->ncpus : maxcpus;
        // Make sure we are not dynamically setting the number of threads
        omp_set_dynamic(0);
        omp_set_num_threads(openmp_numthreads);
        printf("Using %d threads with OpenMP\n\n", openmp_numthreads);
#endif
    } else {
#ifdef _OPENMP
        //        int openmp_numthreads = omp_get_num_threads();
//                int openmp_numthreads = 4;
//                printf("openmp_numthreads : %d\n",openmp_numthreads);
                omp_set_num_threads(1); // Explicitly turn off OpenMP
#endif
    }

```

这里就有点疑惑，项目本身实现了omp，但是检测到只有一个线程，强制改变线程数也没啥用。具体的还要仔细看看代码。



### 1208

好像之前一直检测到一个线程是因为在非并行区，omp_get_num_threads()只能检测到一个线程：

https://blog.csdn.net/gengshenghong/article/details/7003110

omp_get_num_procs()才是正确的使用方法。

所以这里就暂时不纠结了，直接往下读代码。

### 1209

why cmd->cpus is 1?

```
cmd = parseCmdline(argc, argv);
```

这一句里面确定了cmd的参数，但是由于点不进去，只能gdb一点一点的看。

很奇怪，parse中解析了ncpus参数，但是运行命令里面没有这个参数，默认是1，我强制修改了这个参数：

```c++
#ifdef _OPENMP
    cmd->ncpus = omp_get_num_procs();
#endif
```

但是运行时间没什么变化，先继续看后面的代码吧。

更新了check函数，所有的文件都check了，然后发现有一类文件的check有一点问题。



### 1217

实验室局域网坏了，asc连不上，正好这周有些考试也没多少时间干活。

直接在python脚本的级别进行并行：

```bash
Read Header                    === 0.004336 
Generate Dedispersion          === 0.669438 
Dedisperse Subbands            === 8.106017 
fft-search subbands            === 35.642981 
sifting candidates             === 0.124805 
folding candidates             === 23.958407 


real	1m8.983s
user	1m15.204s
sys	0m18.052s
```



在Dedisperse Subbands 并行之后：

```bash
Read Header                    === 0.005490 
Generate Dedispersion          === 0.675505 
Dedisperse Subbands            === 2.151151 
fft-search subbands            === 35.856322 
sifting candidates             === 0.138530 
folding candidates             === 23.293398 


real	1m2.641s
user	1m18.572s
sys	0m16.520s
```

效果还不错，这里有一个问题就是Dedisperse Subbands现在的并行度是能是7，在很多核机器上它可能成为热点。

然后把后面的脚本执行都换成并行的（关闭了presto自带的omp开关）：

```bash
threadController : 1
Read Header                    === 0.004423 
Generate Dedispersion          === 0.654694 
Dedisperse Subbands            === 2.173291 
fft-search subbands            === 6.618843 
sifting candidates             === 0.125564 
folding candidates             === 5.526073 


real	0m15.573s
user	1m41.072s
sys	0m6.532s
```

加速比还不错，这里采用的是from threading import Thread，可以换成其他的线程库试试。

！！注意：这里的log们都没有输出，需要改。



上面的是多线程，感觉程序的io比较多（感觉），就加了个多进程 的版本进行测试：

```bash
threadController : 2
Read Header                    === 0.004823 
Generate Dedispersion          === 0.693231 
Dedisperse Subbands            === 2.180292 
fft-search subbands            === 7.371133 
sifting candidates             === 0.125411 
folding candidates             === 5.741172 


real	0m16.624s
user	1m42.092s
sys	0m7.736s
```

而且还发现，如果上次运行的文件没有delet，运行速度会慢一点点（15s - 18s。16s - 20s。）

对于多线程输出的log信息进行了check，注意修改了fft和acc里面的源代码，把输出时间的信息删除了。



#### 1218

原来没有设置线程数，都是用的系统最大线程数，现在规定最多用两个线程，测测加速比：

```bash
threadNumber : 1
threadController : 0
Read Header                    === 0.004745 
Generate Dedispersion          === 0.698147 
Dedisperse Subbands            === 8.167462 
fft-search subbands            === 36.117673 
sifting candidates             === 0.126861 
folding candidates             === 23.866634 
real	1m9.455s
user	1m15.576s
sys	0m18.248s

threadNumber : 2
threadController : 1
Read Header                    === 0.004749 
Generate Dedispersion          === 0.687718 
Dedisperse Subbands            === 5.090773 
fft-search subbands            === 18.340052 
sifting candidates             === 0.134790 
folding candidates             === 14.080581
real	0m38.853s
user	1m15.668s
sys	0m15.196s

threadNumber : 2
threadController : 2
Read Header                    === 0.005871 
Generate Dedispersion          === 0.677867 
Dedisperse Subbands            === 4.877742 
fft-search subbands            === 18.177540 
sifting candidates             === 0.128444 
folding candidates             === 14.660598 
real	0m39.062s
user	1m13.852s
sys	0m14.528s
```

然后开开4个，8个线程看看

```bash
threadNumber : 4
threadController : 1
Read Header                    === 0.004651 
Generate Dedispersion          === 0.656757 
Dedisperse Subbands            === 2.812546 
fft-search subbands            === 9.494797 
sifting candidates             === 0.123413 
folding candidates             === 8.098120 
real	0m21.689s
user	1m18.644s
sys	0m12.588s


threadController : 2
Read Header                    === 0.007292 
Generate Dedispersion          === 0.679479 
Dedisperse Subbands            === 3.175703 
fft-search subbands            === 9.339058 
sifting candidates             === 0.133920 
folding candidates             === 8.234024 
real	0m22.099s
user	1m18.204s
sys	0m12.084s


threadNumber : 8
threadController : 1
Read Header                    === 0.004564 
Generate Dedispersion          === 0.682917 
Dedisperse Subbands            === 2.209518 
fft-search subbands            === 6.698296 
sifting candidates             === 0.124717 
folding candidates             === 6.465857 
real	0m16.659s
user	1m39.072s
sys	0m7.936s


threadController : 2
Read Header                    === 0.004681 
Generate Dedispersion          === 0.654542 
Dedisperse Subbands            === 2.280438 
fft-search subbands            === 6.756281 
sifting candidates             === 0.135264 
folding candidates             === 6.736000 
real	0m17.054s
user	1m39.872s
sys	0m8.528s
```

可以看出fft-search部分的加速比不错，除了最后的8个线程，基本能达到线性；Dedisperse Subbands和folding candidates的加速比一般，具体原因还要详细分析。



workload2

```bash
threadNumber : 1
threadController : 0
Read Header                    === 0.004555 
Generate Dedispersion          === 0.680577 
Dedisperse Subbands            === 67.029553 
fft-search subbands            === 137.133240 
sifting candidates             === 0.737182 
folding candidates             === 161.940028 
real	6m8.004s
user	6m29.932s
sys	0m57.404s


threadNumber : 2
threadController : 1
Read Header                    === 0.004893 
Generate Dedispersion          === 0.721812 
Dedisperse Subbands            === 38.149455 
fft-search subbands            === 72.775450 
sifting candidates             === 0.764052 
folding candidates             === 90.056885 
real	3m22.992s
user	6m46.880s
sys	0m51.604s

threadController : 2
Read Header                    === 0.004899 
Generate Dedispersion          === 0.697218 
Dedisperse Subbands            === 38.411429 
fft-search subbands            === 69.955862 
sifting candidates             === 0.732876 
folding candidates             === 87.764126 
real	3m18.052s
user	6m39.664s
sys	0m48.044s

threadNumber : 4
threadController : 1
Read Header                    === 0.004809 
Generate Dedispersion          === 0.684369 
Dedisperse Subbands            === 23.693192 
fft-search subbands            === 36.188843 
sifting candidates             === 0.761820 
folding candidates             === 54.648859 
real	1m56.466s
user	7m29.084s
sys	0m39.128s

threadController : 2
Read Header                    === 0.005172 
Generate Dedispersion          === 0.669492 
Dedisperse Subbands            === 23.844496 
fft-search subbands            === 35.982335 
sifting candidates             === 0.709400 
folding candidates             === 56.136693 
real	1m57.832s
user	7m33.400s
sys	0m38.952s

threadNumber 8 :
threadController : 1
Read Header                    === 0.004862 
Generate Dedispersion          === 0.714885 
Dedisperse Subbands            === 23.633118 
fft-search subbands            === 25.297910 
sifting candidates             === 0.756298 
folding candidates             === 51.120357 
real	1m42.007s
user	11m42.932s
sys	0m27.380s


threadController : 2
Read Header                    === 0.005387 
Generate Dedispersion          === 0.680157 
Dedisperse Subbands            === 23.123590 
fft-search subbands            === 25.285303 
sifting candidates             === 0.737998 
folding candidates             === 50.347805 
real	1m40.656s
user	11m41.304s
sys	0m26.700s
```

大数据下8线层的加速比就很差了，线程调度是一方面，还有就是Dedisperse Subbands和folding candidates的执行次数一个是19一个是36，都不算多，可能线程调度的开销就不小，这里测试了一下7个线程的：

```bash
threadController : 1
Read Header                    === 0.004921 
Generate Dedispersion          === 0.705147 
Dedisperse Subbands            === 21.788566 
fft-search subbands            === 27.050926 
sifting candidates             === 0.751524 
folding candidates             === 47.345187 
real	1m38.154s
user	10m31.036s
sys	0m29.580s
```

可以看到De和fold甚至快了一点。

所以下一步还是需要去内部并行。

#### 1219

原来的check所有文件的方法写的太丑了，现在换了一个比较简洁的方法。

在开始研究PRESTO的源代码之前，先看看文档里面的描述：

```
#首先，脉冲星的性质：
#1 信号被星际介质分散
#2 信号是周期的

#脉冲星搜索算法的步骤：
#1 去色散，即测试许多（通常是数千个）可能的色散测量（DM）并对其进行星际延迟校正
#2 使用fft搜索一段时间

#PRESTO中用于脉冲星搜索的三步：
#1 Data Preparation: Interference detection (rfifind) and removal (zapbirds) ,
# de-dispersion (prepdata, prepsubband, and mpiprepsubband), barycentering (via TEMPO)
#2 Searching: Fourier-domain acceleration (accelsearch), single-pulse (single_pulse_search.py)
# and phase-modulation or sideband searches (search_bin).

#3 Folding: Candidate optimization (prepfold) and Time-of-Arrival (TOA) generation (get_TOAs.py).
```

然后提交要求是：

![image-20201219105555686](/Users/ylf9811/Library/Application Support/typora-user-images/image-20201219105555686.png)

ps里面有输出时间信息，把那几行砍掉之后直接test md5值来check。题目要求的是所有文件的文件名一样，然后列出的这几个文件需要提交；现在的check方式，只有.cand文件(二进制文件)过不了check，查看源代码发现是输出的float，存在精度的问题，所以过不了check也是正常，鉴于最后不提交这个文件，就不浪费时间了读进来做check了。

记过分析prepsubband.c的源代码，找到了

```bash
Error in chkfopen(): No such file or directory
   path = 'Sband_DM2.10.dat'
```

的原因，不知道为啥，要读取的时候dat数据不存在，现在怀疑配的环境有问题。关于环境又加了几个TODO。

#### 1220&1221

**都不知道在干什么都**

上午find了accelsearch的热点，主要是来自optimize_accelcand的第一个for循环，里面还有一层for，但是两层加起来大约是10*10，也不太适合并行。

为了确定for1里面没有别的循环，可以做一下timer，accelsearch执行了168次，32秒，一次0.19，time一下时间差不多，继续发掘里面的热点，发现是max_rz_arr_harmonics里面的amoeba，但是很奇怪的是，一次amoeba循环几十次，但是却运行了0.02s，都不知道时间花在哪了。

现在先看fold吧，它每次运行的时间最长，可能是最好收拾的一个。

好家伙

```c++
sh: 1: pstoimg: Permission denied
Error running pstoimg in prepfold_plot(): Success
```

仔细一看log，又有个奇奇怪怪的东西。

最后定位到了prefold.c->prepfold_plot()里面的retval = system(command)这个，执行

```
pstoimg -density 200 -antialias -flip cw -quiet -type png -out %.*s.png %.*s
```

这个命令的时候没有权限然后报错了，可能环境配置的真的有问题，先不管了，先看能不能并行。

fold里面本身有一个加在for上面的omp，但是看top发现线程的利用率并不高。热点是Folded和后面的操作，并且发现执行脚本只占了一半不到的时间，另一半大概是python文件的开销，这个还要再具体测一下。

#### 1222&&1223

形势不太乐观哟，先find一下folding的热点吧。

尝试用一下vtune：

```bash
/home/asc/intel/vtune_profiler_2020.1.0.607630/bin64/vtune -collect hotspots 
```

![image-20201223202255922](/Users/ylf9811/Library/Application Support/typora-user-images/image-20201223202255922.png)

热点居然是这个。。然后clip_times()是backend_common.c里面的函数，apply_gcd没有源文件，经过测试应该就是fftwf_execute_r2r()。不过这俩不太好改都，还是要先想办法并行。。。。

先打开自带的omp试试，方法一是修改python中的脚本，方法二是修改c文件中omp，暂时采用方法一。



#### 1224

先测一下自带的omp效果怎么样（需要打开PFOL看omp对应那一步的时间，因为它本来就不是热点，所以看总时间看不出来）

好家伙，开8线程跑了一个世纪

![image-20201224103543410](/Users/ylf9811/Library/Application Support/typora-user-images/image-20201224103543410.png)

看时间不对应，一看就是里面某个巴拉巴拉还有omp，果然，

![image-20201224103631573](/Users/ylf9811/Library/Application Support/typora-user-images/image-20201224103631573.png)

本来不咋花时间的p5变的很慢了，可能是计时函数的锅，还是跑一下vtune

### 1231

```c++
threadController : 0
Read Header                    === 0.004928 
Generate Dedispersion          === 0.672033 
Dedisperse Subbands            === 8.402275 
realfft                        === 5.552962 
accelsearch                    === 32.698424 
sifting candidates             === 0.123537 
folding candidates             === 27.612722 


real	1m15.576s
user	1m20.608s
sys	0m19.584s
  
threadController : 0
Read Header                    === 0.004879 
Generate Dedispersion          === 0.730260 
Dedisperse Subbands            === 8.333516 
realfft                        === 4.672712 
accelsearch                    === 31.148279 
sifting candidates             === 0.135620 
folding candidates             === 28.281242 


real	1m13.810s
user	1m19.304s
sys	0m18.772s
```

#### 0102

终究还是把2020年的bug留到了新的一年

现在解决三个事，一个是icc答案和gcc不一样，初步猜测是Ofast和ffast-math的是原因；二是使用mkl的fftw；三是

folding里面的并行。显然第三个比较急，启鑫在6148上配环境了，先把多线程搞好测测拓展性。

```c++
threadController : 0
Read Header                    === 0.004921 
Generate Dedispersion          === 0.815033 
Dedisperse Subbands            === 8.990688 
realfft                        === 5.519845 
accelsearch                    === 35.766682 
sifting candidates             === 0.191183 
folding candidates             === 30.777607 


real	1m22.654s
user	1m25.728s
sys	0m17.956s
```

#### 0103

不太妙啊不太妙，fold内部的并行出现了一些问题，来不及写文档了，直接干了。







huaweiyun





omp in c files

```c++
TestData1 

thread 1 -------> 1m10s

thread 2 -------> 1m09s

thread 4 -------> 1m07s

thread 8 -------> 1m09s

thread 16 -------> 1m13s

TestData2

thread 1 -------> 6m47s

thread 2 -------> 6m46s

thread 4 -------> x

thread 8 -------> 6m55s

thread 16 -------> x
```





Parallel in python file

```c++
TestData1
  
  thread 1
  threadController : 1
Read Header                    === 0.009291 
Generate Dedispersion          === 0.804071 
Dedisperse Subbands            === 8.505732 
realfft                        === 4.651085 
accelsearch                    === 26.772940 
sifting candidates             === 0.115611 
folding candidates             === 31.138197
real	1m12.512s
user	1m7.089s
sys	0m10.152s
  
  thread 2
  threadController : 1
Read Header                    === 0.009391 
Generate Dedispersion          === 0.802235 
Dedisperse Subbands            === 4.961636 
realfft                        === 2.355048 
accelsearch                    === 13.764378 
sifting candidates             === 0.110673 
folding candidates             === 17.521174 
real	0m40.035s
user	1m8.135s
sys	0m10.778s
    
    thread 4
    threadController : 1
Read Header                    === 0.009345 
Generate Dedispersion          === 0.794564 
Dedisperse Subbands            === 2.530166 
realfft                        === 1.218100 
accelsearch                    === 6.884483 
sifting candidates             === 0.114649 
folding candidates             === 8.225789 
real	0m20.293s
user	1m8.571s
sys	0m10.380s
      
      thread 8
      threadController : 1
Read Header                    === 0.009293 
Generate Dedispersion          === 0.801965 
Dedisperse Subbands            === 1.399944 
realfft                        === 0.767894 
accelsearch                    === 4.059757 
sifting candidates             === 0.111212 
folding candidates             === 5.562208 
real	0m13.222s
user	1m14.597s
sys	0m10.883s
        
        thread 16
        threadController : 1
Read Header                    === 0.009295 
Generate Dedispersion          === 0.801793 
Dedisperse Subbands            === 1.371154 
realfft                        === 0.533915 
accelsearch                    === 2.919311 
sifting candidates             === 0.112751 
folding candidates             === 3.906745 
real	0m10.168s
user	1m35.041s
sys	0m11.343s
          
          
          
          
          
TestData2
          thread 1
          threadController : 0
Read Header                    === 0.009302 
Generate Dedispersion          === 0.800848 
Dedisperse Subbands            === 81.646578 
realfft                        === 5.008840 
accelsearch                    === 110.613099 
sifting candidates             === 0.633296 
folding candidates             === 208.369890 
real	6m47.599s
user	6m35.853s
sys	0m19.429s
            
            thread 2
            threadController : 1
Read Header                    === 0.009331 
Generate Dedispersion          === 0.799104 
Dedisperse Subbands            === 43.321533 
realfft                        === 3.179594 
accelsearch                    === 57.808893 
sifting candidates             === 0.662162 
folding candidates             === 106.202895 
real	3m32.501s
user	6m43.390s
sys	0m22.892s
          
              thread 4
              threadController : 1
Read Header                    === 0.009208 
Generate Dedispersion          === 0.802750 
Dedisperse Subbands            === 22.139673 
realfft                        === 1.607336 
accelsearch                    === 28.545756 
sifting candidates             === 0.679785 
folding candidates             === 54.164069 
real	1m48.460s
user	6m45.416s
sys	0m23.414s
          
                thread 8
                threadController : 1
Read Header                    === 0.009494 
Generate Dedispersion          === 0.806059 
Dedisperse Subbands            === 14.293050 
realfft                        === 1.088761 
accelsearch                    === 16.042637 
sifting candidates             === 0.663501 
folding candidates             === 32.220073 
real	1m5.640s
user	7m27.879s
sys	0m23.269s
                  
                  thread 16
                  threadController : 1
Read Header                    === 0.009347 
Generate Dedispersion          === 0.804752 
Dedisperse Subbands            === 12.658421 
realfft                        === 0.933014 
accelsearch                    === 11.914109 
sifting candidates             === 0.662286 
folding candidates             === 28.144343 
real	0m55.642s
user	11m28.272s
sys	0m26.203s
```







```c++
now 7788
  TestData1
  threadController : 0
Read Header                    === 0.005434 
Generate Dedispersion          === 0.788359 
Dedisperse Subbands            === 8.216465 
realfft                        === 4.900889 
accelsearch                    === 30.942969 
sifting candidates             === 0.150914 
folding candidates             === 29.973121 
real	1m15.507s
user	1m20.492s
sys	0m20.508s
threadController : 0
Read Header                    === 0.004315 
Generate Dedispersion          === 0.809494 
Dedisperse Subbands            === 8.163039 
realfft                        === 4.833643 
accelsearch                    === 30.673778 
sifting candidates             === 0.150381 
folding candidates             === 27.412909 
real	1m12.572s
user	1m19.304s
sys	0m19.980s
    
    
  TestData2
  threadController : 0
Read Header                    === 0.004169 
Generate Dedispersion          === 0.798403 
Dedisperse Subbands            === 64.531641 
realfft                        === 6.747967 
accelsearch                    === 130.243942 
sifting candidates             === 0.818875 
folding candidates             === 193.285013 
real	6m36.949s
user	6m40.128s
sys	1m15.584s
  
```

