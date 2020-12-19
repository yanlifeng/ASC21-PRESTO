# PRESTO
TODO

（1207）

- [ ] 编译器换成icc
- [ ] fortan换成intel的
- [x] 完成环境配置
- [x] 初步寻找热点
- [x] 做好check
- [x] 测试get_num_threads
- [ ] 修改编译参数
- [ ] 解决python tests的报错
- [ ] 解决prepsubband运行的error
- [x] 尝试python脚本级别的并行
- [ ] 解决CPU使用率低的问题
- [x] 解决只能检测到一个线程的问题
- [ ] 解决_ACCEL_0.cand文件check出错的问题
- [x] 输出log，并做check
- [ ] 解决上次输出没有清空的时候运行变慢（maybe）
- [x] ~~把prepsubb里面的两个脚本拆开~~
- [x] 规定python线程库的threadNumber测试加速比
- [x] 关于第1，3个热点加速比一般的原因
- [ ] check pfd!!
- [ ] 去内部的.c文件并行
- [x] 更换简洁的check方法
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

ps里面有输出时间信息，把那几行砍掉之后直接test md5值来check。

