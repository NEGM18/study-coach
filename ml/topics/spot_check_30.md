# Issue #27: Cleaning Pipeline 30-Chunk Spot-Check

This report verifies that the 7-step cleaning pipeline eliminates headers, metadata,
and OCR noise while preserving genuine lecture content across all pilot courses.

## Cleaning Audit Trail Summary

| Step | Rows Before | Rows After | Delta | Reason |
|---|---|---|---|---|
| `remove_repeating_headers` | 654 | 654 | -0 | drop lines repeating >50% |
| `remove_metadata` | 654 | 654 | -0 | drop page numbers, URLs, emails, and copyright |
| `remove_ocr_garbage` | 654 | 654 | -0 | drop lines with <50% valid letters |
| `normalize_for_training` | 654 | 654 | -0 | apply shared Arabic/Latin normalization |
| `filter_short_chunks` | 654 | 558 | -96 | drop chunks with <5 words |
| `deduplicate_chunks` | 558 | 557 | -1 | drop duplicates with >=90% similarity |
| `tag_language` | 557 | 557 | -0 | tag language as ar, en, or mixed |

## Spot-Check Sample (30 Chunks, Seed 42)

### Chunk 1: `c_os_l203_s04` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 3.4 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Process Concept <br>  <br> An operating system executes a variety of programs: <br> z Batch system – jobs <br> z Time-shared systems – user programs or tasks <br>  <br> Textbook uses the terms job and process almost interchangeably <br>  <br> Process – a program in execution; process execution must  <br> progress in sequential fashion <br>  <br> A process includes: <br> z program counter  <br> z stack <br> z data section
* **Cleaned & Normalized Chunk**:
  > process concept an operating system executes a variety of programs: z batch system – jobs z time-shared systems – user programs or tasks textbook uses the terms job and process almost interchangeably process – a program in execution; process execution must progress in sequential fashion a process includes: z program counter z stack z data section

### Chunk 2: `c_ds_l103_s03` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > Balanced Trees: AVL and Rotations <br> AVL tree maintains balance factor in {-1, 0, 1}. <br> Rotations (LL, RR, LR, RL) restore height balance after insertion. <br> Guarantees O(log n) worst-case search, insertion, and deletion.
* **Cleaned & Normalized Chunk**:
  > balanced trees: avl and rotations avl tree maintains balance factor in {-1, 0, 1}. rotations (ll, rr, lr, rl) restore height balance after insertion. guarantees o(log n) worst-case search, insertion, and deletion.

### Chunk 3: `c_os_l206_s61` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 6.61 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Locking Protocol <br>  <br> Ensure serializability by associating lock with each data item <br> z Follow locking protocol for access control <br>  <br> Locks <br> z Shared – Ti has shared-mode lock (S) on item Q, Ti can read Q but not  <br> write Q <br> z Exclusive – Ti has exclusive-mode lock (X) on Q, Ti can read and write  <br> Q <br>  <br> Require every transaction on item Q acquire appropriate lock <br>  <br> If lock already held, new request may have to wait <br> z Similar to readers-writers algorithm
* **Cleaned & Normalized Chunk**:
  > locking protocol ensure serializability by associating lock with each data item z follow locking protocol for access control locks z shared – ti has shared-mode lock (s) on item q, ti can read q but not write q z exclusive – ti has exclusive-mode lock (x) on q, ti can read and write q require every transaction on item q acquire appropriate lock if lock already held, new request may have to wait z similar to readers-writers algorithm

### Chunk 4: `c_os_l206_s29` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 6.29 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Readers-Writers Problem (Cont.) <br>  <br> The structure of a writer process <br> do { <br> wait (wrt) ; <br> //    writing is performed <br> signal (wrt) ; <br> } while (TRUE);
* **Cleaned & Normalized Chunk**:
  > readers-writers problem (cont.) the structure of a writer process do { wait (wrt) ; // writing is performed signal (wrt) ; } while (true);

### Chunk 5: `c_os_l206_s07` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 6.7 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Race Condition <br>  <br> count++ could be implemented as <br> register1 = count <br> register1 = register1 + 1 <br> count = register1 <br>  <br> count-- could be implemented as <br> register2 = count <br> register2 = register2 - 1 <br> count = register2 <br>  <br> Consider this execution interleaving with “count = 5” initially: <br> S0: producer execute register1 = count <br> {register1 = 5} <br> S1: producer execute register1 = register1 + 1  {register1 = 6}  <br> S2: consumer execute register2 = count <br> {register2 = 5}  <br> S3: consumer execute register2 = register2 - 1 <br> {register2 = 4}  <br> S4: producer execute count = register1 <br> {count = 6 }  <br> S5: consumer execute count = register2 <br> {count = 4}
* **Cleaned & Normalized Chunk**:
  > race condition count++ could be implemented as register1 = count register1 = register1 + 1 count = register1 count-- could be implemented as register2 = count register2 = register2 - 1 count = register2 consider this execution interleaving with “count = 5” initially: s0: producer execute register1 = count {register1 = 5} s1: producer execute register1 = register1 + 1 {register1 = 6} s2: consumer execute register2 = count {register2 = 5} s3: consumer execute register2 = register2 - 1 {register2 = 4} s4: producer execute count = register1 {count = 6 } s5: consumer execute count = register2 {count = 4}

### Chunk 6: `c_os_l203_s38` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 3.38 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Buffering <br>  <br> Queue of messages attached to the link; implemented in one of three  <br> ways <br> 1. Zero capacity – 0 messages  <br> Sender must wait for receiver (rendezvous) <br> 2. Bounded capacity – finite length of n messages  <br> Sender must wait if link full <br> 3. Unbounded capacity – infinite length  <br> Sender never waits
* **Cleaned & Normalized Chunk**:
  > buffering queue of messages attached to the link; implemented in one of three ways 1. zero capacity – 0 messages sender must wait for receiver (rendezvous) 2. bounded capacity – finite length of n messages sender must wait if link full 3. unbounded capacity – infinite length sender never waits

### Chunk 7: `c_os_l202_s42` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 2.42 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Para-virtualization <br>  <br> Presents guest with system similar but not identical to hardware <br>  <br> Guest must be modified to run on paravirtualized hardwareF <br>  <br> Guest can be an OS, or in the case of Solaris 10 applications running in  <br> containers
* **Cleaned & Normalized Chunk**:
  > para-virtualization presents guest with system similar but not identical to hardware guest must be modified to run on paravirtualized hardwaref guest can be an os, or in the case of solaris 10 applications running in containers

### Chunk 8: `c_os_l202_s21` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 2.21 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Examples of Windows and Unix System Calls
* **Cleaned & Normalized Chunk**:
  > examples of windows and unix system calls

### Chunk 9: `c_os_l210_s02` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 10.2 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Chapter 10:  File-System Interface <br>  <br> File Concept <br>  <br> Access Methods <br>  <br> Directory Structure <br>  <br> File-System Mounting <br>  <br> File Sharing <br>  <br> Protection
* **Cleaned & Normalized Chunk**:
  > chapter 10: file-system interface file concept access methods directory structure file-system mounting file sharing protection

### Chunk 10: `c_os_l201_s02` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 1.2 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Chapter 1: Introduction <br>  <br> What Operating Systems Do <br>  <br> Computer-System Organization <br>  <br> Computer-System Architecture <br>  <br> Operating-System Structure <br>  <br> Operating-System Operations <br>  <br> Process Management <br>  <br> Memory Management <br>  <br> Storage Management <br>  <br> Protection and Security <br>  <br> Distributed Systems <br>  <br> Special-Purpose Systems <br>  <br> Computing Environments <br>  <br> Open-Source Operating Systems
* **Cleaned & Normalized Chunk**:
  > chapter 1: introduction what operating systems do computer-system organization computer-system architecture operating-system structure operating-system operations process management memory management storage management protection and security distributed systems special-purpose systems computing environments open-source operating systems

### Chunk 11: `c_ds_l104_s04` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Shortest Paths: Dijkstra Algorithm <br> Single-source shortest paths with non-negative edge weights. <br> Maintains distance estimates and explores minimum using priority queue. <br> Time complexity O((V + E) log V) with binary heap. <br> Confidential - University Course | Page 4 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > shortest paths: dijkstra algorithm single-source shortest paths with non-negative edge weights. maintains distance estimates and explores minimum using priority queue. time complexity o((v + e) log v) with binary heap.

### Chunk 12: `c_os_l202_s28` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 2.28 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Operating System Design and Implementation (Cont) <br>  <br> Important principle to separate <br> Policy:   What will be done?  <br> Mechanism:  How to do it? <br>  <br> Mechanisms determine how to do something, policies decide what will be  <br> done <br> z The separation of policy from mechanism is a very important principle, it  <br> allows maximum flexibility if policy decisions are to be changed later
* **Cleaned & Normalized Chunk**:
  > operating system design and implementation (cont) important principle to separate policy: what will be done? mechanism: how to do it? mechanisms determine how to do something, policies decide what will be done z the separation of policy from mechanism is a very important principle, it allows maximum flexibility if policy decisions are to be changed later

### Chunk 13: `c_os_l206_s02` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 6.2 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Module 6: Process Synchronization <br>  <br> Background <br>  <br> The Critical-Section Problem <br>  <br> Peterson’s Solution <br>  <br> Synchronization Hardware <br>  <br> Semaphores <br>  <br> Classic Problems of Synchronization <br>  <br> Monitors <br>  <br> Synchronization Examples  <br>  <br> Atomic Transactions
* **Cleaned & Normalized Chunk**:
  > module 6: process synchronization background the critical-section problem peterson’s solution synchronization hardware semaphores classic problems of synchronization monitors synchronization examples atomic transactions

### Chunk 14: `c_os_l206_s17` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 6.17 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Bounded-waiting Mutual Exclusion with TestandSet() <br> do {  <br> waiting[i] = TRUE;  <br> key = TRUE;  <br> while (waiting[i] && key)  <br> key = TestAndSet(&lock);  <br> waiting[i] = FALSE;  <br> // critical section  <br> j = (i + 1) % n;  <br> while ((j != i) && !waiting[j])  <br> j = (j + 1) % n;  <br> if (j == i)  <br> lock = FALSE;  <br> else  <br> waiting[j] = FALSE;  <br> // remainder section  <br> } while (TRUE);
* **Cleaned & Normalized Chunk**:
  > bounded-waiting mutual exclusion with testandset() do { waiting = true; key = true; while (waiting && key) key = testandset(&lock); waiting = false; // critical section while ((j != i) && !waiting ) if (j == i) lock = false; else waiting = false; // remainder section } while (true);

### Chunk 15: `c_os_l212_s03` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 12.3 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Objectives <br>  <br> Describe the physical structure of secondary and tertiary storage devices  <br> and the resulting effects on the uses of the devices <br>  <br> Explain the performance characteristics of mass-storage devices <br>  <br> Discuss operating-system services provided for mass storage, including  <br> RAID and HSM
* **Cleaned & Normalized Chunk**:
  > objectives describe the physical structure of secondary and tertiary storage devices and the resulting effects on the uses of the devices explain the performance characteristics of mass-storage devices discuss operating-system services provided for mass storage, including raid and hsm

### Chunk 16: `c_ds_l104_s01` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> CS201 Lecture 4: Hashing and Graphs <br> Advanced structures and graph theory. <br> Instructor: Dr. Ahmed Hassan - ahmed@univ.edu.eg <br> Confidential - University Course | Page 1 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > cs201 lecture 4: hashing and graphs advanced structures and graph theory. instructor: dr. ahmed hassan -

### Chunk 17: `c_os_l205_s26` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 5.26 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Example of Multilevel Feedback Queue <br>  <br> Three queues:  <br> z Q0 – RR with time quantum 8 milliseconds <br> z Q1 – RR time quantum 16 milliseconds <br> z Q2 – FCFS <br>  <br> Scheduling <br> z A new job enters queue Q0 which is served FCFS. When it gains CPU,  <br> job receives 8 milliseconds.  If it does not finish in 8 milliseconds, job is  <br> moved to queue Q1. <br> z At Q1 job is again served FCFS and receives 16 additional milliseconds.   <br> If it still does not complete, it is preempted and moved to queue Q2.
* **Cleaned & Normalized Chunk**:
  > example of multilevel feedback queue three queues: z q0 – rr with time quantum 8 milliseconds z q1 – rr time quantum 16 milliseconds z q2 – fcfs scheduling z a new job enters queue q0 which is served fcfs. when it gains cpu, job receives 8 milliseconds. if it does not finish in 8 milliseconds, job is moved to queue q1. z at q1 job is again served fcfs and receives 16 additional milliseconds. if it still does not complete, it is preempted and moved to queue q2.

### Chunk 18: `c_os_l209_s69` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 9.69 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Solaris  <br>  <br> Maintains a list of free pages to assign faulting processes <br>  <br> Lotsfree – threshold parameter (amount of free memory) to begin paging <br>  <br> Desfree – threshold parameter to increasing paging <br>  <br> Minfree – threshold parameter to being swapping <br>  <br> Paging is performed by pageout process <br>  <br> Pageout scans pages using modified clock algorithm <br>  <br> Scanrate is the rate at which pages are scanned. This ranges from  <br> slowscan to fastscan <br>  <br> Pageout is called more frequently depending upon the amount of free  <br> memory available
* **Cleaned & Normalized Chunk**:
  > solaris maintains a list of free pages to assign faulting processes lotsfree – threshold parameter (amount of free memory) to begin paging desfree – threshold parameter to increasing paging minfree – threshold parameter to being swapping paging is performed by pageout process pageout scans pages using modified clock algorithm scanrate is the rate at which pages are scanned. this ranges from slowscan to fastscan pageout is called more frequently depending upon the amount of free memory available

### Chunk 19: `c_os_l206_s04` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 6.4 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Background <br>  <br> Concurrent access to shared data may result in data  <br> inconsistency <br>  <br> Maintaining data consistency requires mechanisms to  <br> ensure the orderly execution of cooperating processes <br>  <br> Suppose that we wanted to provide a solution to the  <br> consumer-producer problem that fills all the buffers. We  <br> can do so by having an integer count that keeps track of  <br> the number of full buffers.  Initially, count is set to 0. It is <br> incremented by the producer after it produces a new  <br> buffer and is decremented by the consumer after it  <br> consumes a buffer.
* **Cleaned & Normalized Chunk**:
  > background concurrent access to shared data may result in data inconsistency maintaining data consistency requires mechanisms to ensure the orderly execution of cooperating processes suppose that we wanted to provide a solution to the consumer-producer problem that fills all the buffers. we can do so by having an integer count that keeps track of the number of full buffers. initially, count is set to 0. it is incremented by the producer after it produces a new buffer and is decremented by the consumer after it consumes a buffer.

### Chunk 20: `c_os_l210_s34` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 10.34 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> File Sharing <br>  <br> Sharing of files on multi-user systems is desirable <br>  <br> Sharing may be done through a protection scheme <br>  <br> On distributed systems, files may be shared across a network <br>  <br> Network File System (NFS) is a common distributed file-sharing method
* **Cleaned & Normalized Chunk**:
  > file sharing sharing of files on multi-user systems is desirable sharing may be done through a protection scheme on distributed systems, files may be shared across a network network file system (nfs) is a common distributed file-sharing method

### Chunk 21: `c_os_l206_s64` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 6.64 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Timestamp-based Protocol Implementation <br>  <br> Data item Q gets two timestamps <br> z W-timestamp(Q) – largest timestamp of any transaction that executed  <br> write(Q) successfully <br> z R-timestamp(Q) – largest timestamp of successful read(Q) <br> z Updated whenever read(Q) or write(Q) executed <br>  <br> Timestamp-ordering protocol assures any conflicting read and write <br> executed in timestamp order <br>  <br> Suppose Ti executes read(Q) <br> z If TS(Ti) < W-timestamp(Q), Ti needs to read value of Q that was  <br> already overwritten <br>  read operation rejected and Ti rolled back <br> z If TS(Ti) ≥W-timestamp(Q) <br>  read executed, R-timestamp(Q) set to max(R-timestamp(Q), TS(Ti))
* **Cleaned & Normalized Chunk**:
  > timestamp-based protocol implementation data item q gets two timestamps z w-timestamp(q) – largest timestamp of any transaction that executed write(q) successfully z r-timestamp(q) – largest timestamp of successful read(q) z updated whenever read(q) or write(q) executed timestamp-ordering protocol assures any conflicting read and write executed in timestamp order suppose ti executes read(q) z if ts(ti) < w-timestamp(q), ti needs to read value of q that was already overwritten  read operation rejected and ti rolled back z if ts(ti) ≥w-timestamp(q)  read executed, r-timestamp(q) set to max(r-timestamp(q), ts(ti))

### Chunk 22: `c_ai_l303_s01` (Course 3, Lang: `en`)
* **Original Slide Text**:
  > CS482 Constraint Satisfaction and Logic <br> CSPs and Propositional Logic. <br> Course material: https://ai482.univ.edu.eg/logic
* **Cleaned & Normalized Chunk**:
  > cs482 constraint satisfaction and logic csps and propositional logic. course material:

### Chunk 23: `c_os_l204_s15` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 4.15 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> One-to-One <br>  <br> Each user-level thread maps to kernel thread <br>  <br> Examples <br> z Windows NT/XP/2000 <br> z Linux <br> z Solaris 9 and later
* **Cleaned & Normalized Chunk**:
  > one-to-one each user-level thread maps to kernel thread examples z windows nt/xp/2000 z linux z solaris 9 and later

### Chunk 24: `c_os_l208_s19` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 8.19 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Fragmentation <br>  <br> External Fragmentation – total memory space exists to satisfy a  <br> request, but it is not contiguous <br>  <br> Internal Fragmentation – allocated memory may be slightly larger  <br> than requested memory; this size difference is memory internal to a  <br> partition, but not being used <br>  <br> Reduce external fragmentation by compaction <br> z Shuffle memory contents to place all free memory together in  <br> one large block <br> z Compaction is possible only if relocation is dynamic, and is  <br> done at execution time <br> z I/O problem <br>  Latch job in memory while it is involved in I/O <br>  Do I/O only into OS buffers
* **Cleaned & Normalized Chunk**:
  > fragmentation external fragmentation – total memory space exists to satisfy a request, but it is not contiguous internal fragmentation – allocated memory may be slightly larger than requested memory; this size difference is memory internal to a partition, but not being used reduce external fragmentation by compaction z shuffle memory contents to place all free memory together in one large block z compaction is possible only if relocation is dynamic, and is done at execution time z i/o problem  latch job in memory while it is involved in i/o  do i/o only into os buffers

### Chunk 25: `c_os_l204_s10` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 4.10 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> User Threads <br>  <br> Thread management done by user-level threads library <br>  <br> Three primary thread libraries: <br> z <br> POSIX Pthreads <br> z <br> Win32 threads <br> z <br> Java threads
* **Cleaned & Normalized Chunk**:
  > user threads thread management done by user-level threads library three primary thread libraries: z posix pthreads z win32 threads z java threads

### Chunk 26: `c_os_l205_s53` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 5.53 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Time-Slicing <br> Since the JVM Doesn’t Ensure Time-Slicing, the yield() Method  <br> May Be Used: <br> while (true) { <br> // perform CPU-intensive task <br> . . . <br> Thread.yield(); <br> } <br> This Yields Control to Another Thread of Equal Priority
* **Cleaned & Normalized Chunk**:
  > time-slicing since the jvm doesn’t ensure time-slicing, the yield() method may be used: while (true) { // perform cpu-intensive task thread.yield(); this yields control to another thread of equal priority

### Chunk 27: `c_os_l208_s15` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 8.15 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Contiguous Allocation <br>  <br> Main memory usually into two partitions: <br> z Resident operating system, usually held in low memory with  <br> interrupt vector <br> z User processes then held in high memory <br>  <br> Relocation registers used to protect user processes from each  <br> other, and from changing operating-system code and data <br> z Base register contains value of smallest physical address <br> z Limit register contains range of logical addresses – each  <br> logical address must be less than the limit register  <br> z MMU maps logical address dynamically
* **Cleaned & Normalized Chunk**:
  > contiguous allocation main memory usually into two partitions: z resident operating system, usually held in low memory with interrupt vector z user processes then held in high memory relocation registers used to protect user processes from each other, and from changing operating-system code and data z base register contains value of smallest physical address z limit register contains range of logical addresses – each logical address must be less than the limit register z mmu maps logical address dynamically

### Chunk 28: `c_os_l202_s27` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 2.27 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Operating System Design and Implementation <br>  <br> Design and Implementation of OS not “solvable”, but some approaches  <br> have proven successful <br>  <br> Internal structure of different Operating Systems  can vary widely <br>  <br> Start by defining goals and specifications  <br>  <br> Affected by choice of hardware, type of system <br>  <br> User goals and System goals <br> z User goals – operating system should be convenient to use, easy to  <br> learn, reliable, safe, and fast <br> z System goals – operating system should be easy to design, implement,  <br> and maintain, as well as flexible, reliable, error-free, and efficient
* **Cleaned & Normalized Chunk**:
  > operating system design and implementation design and implementation of os not “solvable”, but some approaches have proven successful internal structure of different operating systems can vary widely start by defining goals and specifications affected by choice of hardware, type of system user goals and system goals z user goals – operating system should be convenient to use, easy to learn, reliable, safe, and fast z system goals – operating system should be easy to design, implement, and maintain, as well as flexible, reliable, error-free, and efficient

### Chunk 29: `c_os_l209_s17` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 9.17 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Process Creation <br>  <br> Virtual memory allows other benefits during process creation: <br> - Copy-on-Write <br> - Memory-Mapped Files (later)
* **Cleaned & Normalized Chunk**:
  > process creation virtual memory allows other benefits during process creation: - copy-on-write - memory-mapped files (later)

### Chunk 30: `c_os_l202_s35` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > 2.35 <br> Silberschatz, Galvin and Gagne ©2009 <br> Operating System Concepts – 8th Edition <br> Microkernel System Structure  <br>  <br> Moves as much from the kernel into “user” space <br>  <br> Communication takes place between user modules using message passing <br>  <br> Benefits: <br> z Easier to extend a microkernel <br> z Easier to port the operating system to new architectures <br> z More reliable (less code is running in kernel mode) <br> z More secure <br>  <br> Detriments: <br> z Performance overhead of user space to kernel space communication
* **Cleaned & Normalized Chunk**:
  > microkernel system structure moves as much from the kernel into “user” space communication takes place between user modules using message passing benefits: z easier to extend a microkernel z easier to port the operating system to new architectures z more reliable (less code is running in kernel mode) z more secure detriments: z performance overhead of user space to kernel space communication
