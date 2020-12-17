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
- [ ] 输出log，并做check
- [ ] 解决上次输出没有清空的时候运行变慢（maybe）
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





