# Lecture Topic Classification Labeling Guide

This document establishes the official annotation protocol and taxonomy definitions for **Model C (Topic Classifier)** across the three pilot courses:
1. **Data Structures & Algorithms (`ds`)**
2. **Operating Systems (`os`)**
3. **Artificial Intelligence & Machine Learning (`ai`)**

All annotators and automated pre-labeling systems must adhere strictly to these definitions and boundary rules.

---

## 1. General Annotation Rules

1. **Granularity**: Annotations are assigned at the chunk level (typically representing one slide or a coherent slide section).
2. **Exclusivity**: Assign exactly one primary topic per chunk. If a slide bridges two topics, assign the topic corresponding to the core theoretical mechanism or majority of lines.
3. **Language Invariance**: Slides in Egyptian universities frequently mix standard English technical terminology with Egyptian Arabic explanations (code-switching). Classification must depend on the conceptual content, not the language or script.
4. **Normalized Representation**: Before annotating, text is viewed in its normalized form as produced by `ml_core.text_normalize`.

---

## 2. Explicit Rules for Assigning "other"

The `"other"` category exists to isolate administrative and non-examinable pedagogical metadata from domain syllabus content. A chunk **MUST** be labeled as `"other"` if its primary purpose falls into any of the following:

1. **Course Administration & Logistics**:
   - Instructor names, emails, office hours, teaching assistant (TA) contacts.
   - Lecture hall locations, Zoom links, LMS/Google Classroom codes.
2. **Grading & Assessment Policies**:
   - Grade breakdown tables (e.g., 20% Midterm, 10% Quizzes, 30% Project, 40% Final).
   - Attendance requirements, bonus policies, late submission penalties.
3. **Exam Rules & Schedules**:
   - Dates, room assignments, cheat-sheet rules, calculator permissions.
4. **Textbooks & References**:
   - Recommended reading lists, citation pages, textbook covers, library links.
5. **Title, Agenda & Transition Slides**:
   - Standalone lecture cover slides ("Lecture 4: Sorting Algorithms", date, author).
   - Table of contents or outline slides without substantive conceptual definitions ("Today's Agenda: 1. Review 2. BFS 3. Summary").
   - Q&A, "Thank You", or blank transition slides.

> **Rule of Thumb**: If removing this slide from a student's study deck would NOT deprive them of examinable technical concepts or algorithmic steps, label it `"other"`.

---

## 3. Course 1: Data Structures & Algorithms (`ds`)

### 101. Arrays and Dynamic Arrays
* **Definition**: Contiguous sequential memory structures, direct indexing, amortized time complexity analysis for array resizing (geometric expansion), and bounds checking.
* **Example 1 (English)**:
  > Dynamic Array Resizing: When capacity is reached, allocate a new array of double size `2N`, copy existing elements, and insert the new item. Amortized cost per insertion is O(1).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ array العادية حجمها ثابت في الـ memory. لكن الـ dynamic array بتعمل resize لما تتملي، فبتعمل allocate لمساحة جديدة ضعف القديمة وبتنقل الـ elements.

### 102. Linked Lists
* **Definition**: Pointer-based linear nodes, singly/doubly/circular linked lists, head/tail pointers, traversal, node insertion, node deletion, and Floyd's cycle detection.
* **Example 1 (English)**:
  > Singly Linked List: Each node contains a data payload and a `next` pointer. Insertion at head is O(1), but search requires traversing from head with O(n) time.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في الـ Doubly Linked List كل node عندها pointer على الـ next و pointer على الـ prev. الميزة إنك تقدر تعمل delete للـ node في O(1) لو معاك الـ pointer بتاعها.

### 103. Stacks and Queues
* **Definition**: Abstract data types adhering to LIFO (Last-In-First-Out) and FIFO (First-In-First-Out), push/pop/peek operations, circular buffers, and infix/postfix expression evaluation.
* **Example 1 (English)**:
  > Stack ADT: LIFO behavior. Useful in function call stack tracking, parenthesization validation, and depth-first exploration.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ Queue بتشتغل بنظام FIFO: أول element يدخل هو أول element يخرج. الـ enqueue بنضيف في الـ rear والـ dequeue بنحذف من الـ front.

### 104. Recursion and Backtracking
* **Definition**: Self-referencing functions, base condition termination, call stack frames, recurrence equations, tree search backtracking (N-Queens, Sudoku, subset generation).
* **Example 1 (English)**:
  > Recursive Backtracking: Explore each candidate choice down the recursion tree. If the state violates constraints, backtrack by undoing the choice and try the next alternative.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > أهم حاجة في الـ Recursion هي الـ Base Case عشان نمنع الـ Stack Overflow. لو مفيش base case الفانكشن هتفضل تنادي نفسها لحد ما الـ memory تخلص.

### 105. Trees and Binary Search Trees
* **Definition**: Non-linear hierarchical tree structures, parent-child edges, root, leaves, traversals (preorder, inorder, postorder, level-order), and BST search property (left < root < right).
* **Example 1 (English)**:
  > Binary Search Tree (BST) Invariant: For any node X, all keys in the left subtree are smaller than X.key, and all keys in the right subtree are greater than X.key.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ Inorder traversal في الـ Binary Search Tree بيطلع الـ elements مترتبين ترتيب تصاعدي (sorted order).

### 106. Balanced Trees
* **Definition**: Self-balancing BSTs (AVL trees, Red-Black trees), balance factor, left and right rotations, height preservation O(log n) guarantees.
* **Example 1 (English)**:
  > AVL Tree: Balance factor of any node is height(left) - height(right) and must belong to {-1, 0, 1}. Single or double rotations restore invariant upon insertion.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > لما الـ Balance Factor يزيد عن 1 أو يقل عن -1 في الـ AVL tree، بنعمل rotation سواء Left-Left أو Left-Right عشان نرجع الشجرة متوازنة.

### 107. Heaps and Priority Queues
* **Definition**: Complete binary trees satisfying heap order (min-heap or max-heap), compact array representation (`parent = i/2`, `left = 2i`), sift-up, sift-down, heapify O(n), and heapsort.
* **Example 1 (English)**:
  > Max-Heap Property: Every parent node has a key greater than or equal to its children. Extract-max swaps root with last element and calls sift-down in O(log n).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > بنمثل الـ Binary Heap جوه array عادي بدون pointers لأنها Complete Binary Tree. الـ root بيكون في index 1 وأولاده في 2i و 2i+1.

### 108. Hash Tables and Hashing
* **Definition**: Key-value mapping via hash functions, load factor `alpha = n/m`, collision handling strategies (separate chaining, open addressing via linear/quadratic probing, double hashing).
* **Example 1 (English)**:
  > Collision Resolution via Chaining: Colliding keys are stored in a linked list at the bucket index. Expected lookup time remains O(1) assuming uniform hashing.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > لو حصل collision في الـ Open Addressing بنستخدم Linear Probing بندور على أول slot فاضي في الـ table عشان نحط فيه الـ key الجديد.

### 109. Graphs and Graph Traversals
* **Definition**: Vertices and edges (directed, undirected, weighted), representation by adjacency matrix vs adjacency list, Breadth-First Search (BFS), Depth-First Search (DFS), topological sort.
* **Example 1 (English)**:
  > Graph Traversal: BFS uses a FIFO queue and visits vertices level-by-level, finding unweighted shortest paths. DFS utilizes recursion or an explicit LIFO stack.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في الـ BFS بنبدأ من الـ start node ونحط جيرانها في Queue ونعملهم mark as visited عشان منلفش في cycles.

### 110. Shortest Paths and Minimum Spanning Trees
* **Definition**: Weighted graph algorithms: Dijkstra's single-source shortest path (non-negative edges), Bellman-Ford, Prim's and Kruskal's algorithms for MST with Disjoint-Set Union (DSU).
* **Example 1 (English)**:
  > Kruskal's Algorithm: Sort all graph edges by ascending weight. Greedily add edges that connect disjoint components, detecting cycles using Union-Find.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > خوارزمية Dijkstra بتستخدم Priority Queue عشان تجيب الـ shortest path من الـ source لكل الـ nodes بشرط ميكونش فيه negative weights.

### 111. Sorting and Searching Algorithms
* **Definition**: Comparison sorts (Merge Sort, Quick Sort, Insertion Sort, Heap Sort) with O(n log n) limits, non-comparison sorts (Counting Sort, Radix Sort), and binary search.
* **Example 1 (English)**:
  > Quick Sort: Select a pivot, partition elements into sub-arrays less than and greater than the pivot, then recursively sort partitions. Average runtime is O(n log n).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في الـ Binary Search لازم الـ array تكون sorted الأول. بنقارن الـ target بالـ middle element ونقسم مجال البحث بالنصف في كل خطوة.

### 112. Asymptotic Analysis and Big-O
* **Definition**: Formal asymptotic notations: O, Omega, Theta; growth orders, best/worst/average case complexity, space complexity, Master Theorem for divide-and-conquer recurrences.
* **Example 1 (English)**:
  > Master Theorem: For recurrences T(n) = aT(n/b) + f(n), compare f(n) with n^(log_b a) across the three canonical cases to determine tight asymptotic bounds.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > بنحسب الـ Big-O عشان نعرف أداء الـ algorithm لما حجم الـ input n يكبر جداً، وبنهمل الـ constants والـ lower order terms.

### 113. other
* **Definition**: Non-technical course orientation, administrative slides, grading sheets, exam dates, textbook links, and slide headers.
* **Example 1 (English)**:
  > CS201 Data Structures — Fall 2026. Instructor: Dr. Ahmed. Midterm Exam: Week 7 (30%), Final Exam (40%), Lab Assignments (30%).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > مواعيد تسليم الشيتات: كل يوم ثلاثاء قبل الساعة 12 بالليل على المودل. أي تسليم متأخر هيتخصم منه 10% لكل يوم تأخير.

---

## 4. Course 2: Operating Systems (`os`)

### 201. OS Architecture and System Calls
* **Definition**: Kernel vs user mode execution, CPU ring levels, hardware interrupts, trap instructions, system call dispatch table, and monolithic vs microkernel architectures.
* **Example 1 (English)**:
  > Dual-Mode Operation: Hardware timer and mode bit protect CPU resources. Switching from user mode to kernel mode requires a software interrupt or system call instruction (e.g., `sysenter`, `syscall`).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > لما الـ user program يحتاج يقرأ فايل من الـ disk، بيعمل System Call زي `read()` والـ CPU بيتحول من User Mode إلى Kernel Mode عن طريق Trap.

### 202. Processes and Process Management
* **Definition**: Process abstraction, Process Control Block (PCB), execution states (New, Ready, Running, Waiting, Terminated), context switching, `fork()` and `exec()` APIs, zombie/orphan processes.
* **Example 1 (English)**:
  > Context Switch: The OS saves the CPU registers and program counter of the currently executing process into its PCB and restores state from the scheduled process's PCB.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > أمر `fork()` في لينكس بيعمل Child Process جديدة نسخة طبق الأصل من الـ Parent، وبيرجع 0 للطفل والـ PID بتاعه للـ Parent.

### 203. Threads and Concurrency
* **Definition**: Lightweight execution units within a shared address space, thread control blocks (TCBs), user-level vs kernel-level threads, multithreading mapping models (1:1, M:1, M:N), POSIX pthreads.
* **Example 1 (English)**:
  > Threads vs Processes: Threads share text segment, heap, and open file descriptors, but each thread maintains an independent program counter, registers, and private stack.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ Multithreading بيسمح للبرنامج يستغل الـ Multi-core CPUs، بحيث كل thread ينفذ task في نفس الوقت على core مختلف مع مشاركة الـ Memory.

### 204. CPU Scheduling Algorithms
* **Definition**: Long-term, medium-term, and short-term schedulers; preemptive vs non-preemptive metrics (turnaround, waiting time, throughput); FCFS, SJF, SRTF, Round Robin (time quantum), Multilevel Feedback Queues.
* **Example 1 (English)**:
  > Round Robin Scheduling: Each ready process receives a fixed time slice (quantum q). If the CPU burst exceeds q, the process is preempted and placed at the tail of the ready queue.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > خوارزمية Shortest Job First (SJF) بتدي أقل Average Waiting Time بس عيبها إننا صعب نتوقع طول الـ Next CPU Burst بدقة.

### 205. Process Synchronization and Mutexes
* **Definition**: Critical Section Problem, race conditions, mutual exclusion conditions (progress, bounded waiting), software solutions (Peterson's algorithm), atomic hardware primitives (Test-and-Set, Compare-and-Swap), mutex locks.
* **Example 1 (English)**:
  > Critical Section Problem: A solution must satisfy Mutual Exclusion, Progress, and Bounded Waiting. Mutex locks provide binary lock acquisition and release primitives.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ Race Condition بتحصل لما اتنين threads يقرأوا ويكتبوا في نفس الـ Shared Variable في نفس الوقت، والنتيجة بتعتمد على مين اللي خلص الأول.

### 206. Semaphores and Monitors
* **Definition**: Dijkstra's counting and binary semaphores, atomic `wait()` (P) and `signal()` (V) operations, condition variables, monitor constructs, Producer-Consumer and Reader-Writer solutions.
* **Example 1 (English)**:
  > Counting Semaphore: An integer variable initialized to resource pool size N. `wait(S)` decrements S and blocks if negative; `signal(S)` increments S and unblocks waiting threads.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في مسألة الـ Producer-Consumer بنستخدم 2 semaphores: واحد اسمه `empty` بيعد الـ slots الفاضية، والتاني اسمه `full` بيعد الـ items المنتجة.

### 207. Deadlocks
* **Definition**: Four Coffman deadlock conditions (Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait), Resource Allocation Graphs (RAG), prevention, avoidance via Banker's Algorithm (safe states), detection and recovery.
* **Example 1 (English)**:
  > Banker's Algorithm: Test whether granting a resource request leaves the system in a safe sequence where every process can still obtain its maximum claimed resources and terminate.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > عشان يحصل Deadlock لازم الـ 4 شروط يتحققوا مع بعض. لو قدرنا نكسر شرط واحد بس زي الـ Circular Wait بنضمن إن السيستم ميوقفش أبداً.

### 208. Main Memory Management and Paging
* **Definition**: Address binding, logical vs physical addresses, contiguous allocation, external and internal fragmentation, paging, Page Table Entries (PTE), Translation Lookaside Buffer (TLB) hit ratios.
* **Example 1 (English)**:
  > Paging Architecture: Logical address is split into page number (p) and offset (d). The MMU looks up p in the page table to find the corresponding physical frame number (f).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ TLB هو كاش سريع جداً جوه الـ CPU بيخزن الـ translations الأخيرة عشان منضطرش نروح للـ Memory مرتين في كل access.

### 209. Virtual Memory and Page Replacement
* **Definition**: Demand paging, page fault service routine, Belady's anomaly, page replacement policies (FIFO, Optimal, LRU, Clock / Second-Chance), working set model, and thrashing.
* **Example 1 (English)**:
  > Least Recently Used (LRU) Replacement: Replaces the page that has not been referenced for the longest period. It is free from Belady's anomaly but requires hardware stack or timestamp support.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > لما الـ Page متبقاش موجودة في الـ RAM بيحصل Page Fault، فالـ OS بينقل الـ Process لحالة الـ Wait وبيجيب الـ page المطلوبة من الـ Hard Disk.

### 210. File System Interface and Implementation
* **Definition**: File attributes, operations, directory implementations (linear, hash), index nodes (inodes), allocation methods (contiguous, linked, indexed with direct/indirect blocks), journaling and consistency.
* **Example 1 (English)**:
  > UNIX Inode Structure: Contains file metadata, 12 direct block pointers, a single indirect block pointer, a double indirect pointer, and a triple indirect block pointer.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ Inode بيخزن كل بيانات الملف زي الـ size والـ permissions ومكان الـ blocks على الهارد، لكن اسم الملف بيتخزن في الـ Directory entry مش في الـ inode.

### 211. Mass-Storage and Disk Scheduling
* **Definition**: Magnetic disk mechanics (seek time, rotational latency), SSD flash architecture (wear leveling, TRIM), disk arm scheduling algorithms (FCFS, SSTF, SCAN / Elevator, C-SCAN, LOOK), RAID levels (0, 1, 5, 6).
* **Example 1 (English)**:
  > SCAN (Elevator) Algorithm: Disk arm moves in one direction servicing requests until reaching the edge, then reverses direction servicing pending cylinders. Prevents starvation seen in SSTF.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ Seek Time هو الوقت اللي بتاخده رأس القراءة عشان تتحرك للـ Track المطلوب على أسطوانة الهارد ديسك، وهو أكبر عامل مؤثر في بطء القراءة.

### 212. I/O Systems and Device Management
* **Definition**: I/O hardware interfaces, memory-mapped I/O, polling vs interrupt-driven I/O, Direct Memory Access (DMA) controllers, device drivers, and buffering/caching.
* **Example 1 (English)**:
  > Direct Memory Access (DMA): Device controller transfers an entire block of data directly to/from main memory without CPU intervention, generating an interrupt upon completion.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > بدل ما الـ CPU يفضل يضيع وقته في Polling على جهاز بطيء، بنستخدم الـ Interrupts بحيث الجهاز ينادي الـ CPU لما يخلص داتا.

### 213. other
* **Definition**: Non-examinable slides: course outline, syllabus, instructor office hours, lab tool tutorials (e.g., Linux bash setup), grading distribution, and title cards.
* **Example 1 (English)**:
  > Operating Systems Course Syllabus — Dr. Tarek. Midterm: 25%, Labs & Assignments: 25%, Final Examination: 50%. Required Text: Silberschatz, Operating System Concepts 10th Ed.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > مواعيد المعمل: السكشن يوم الأحد الساعة 10 صباحاً في معمل 3. برجاء تسطيب أوبونتو أو VirtualBox قبل ميعاد السكشن القادم.

---

## 5. Course 3: Artificial Intelligence & Machine Learning (`ai`)

### 301. Intelligent Agents and Search
* **Definition**: Rational agents, sensors, actuators, PEAS specifications (Performance, Environment, Actuators, Sensors), environment dimensions (deterministic, static, discrete), and state-space formulation.
* **Example 1 (English)**:
  > PEAS Framework for Automated Taxi: Performance metric (safety, speed, comfort), Environment (roads, pedestrians, weather), Actuators (steering, accelerator, brake), Sensors (cameras, LIDAR, GPS).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ Rational Agent هو اللي بيختار الـ action اللي يعظم الـ expected performance بتاعه بناء على الـ percept sequence اللي استقبلها.

### 302. Uninformed Search
* **Definition**: Blind search strategies without domain knowledge: Breadth-First Search (BFS), Depth-First Search (DFS), Depth-Limited Search (DLS), Iterative Deepening DFS (IDDFS), Uniform-Cost Search (UCS).
* **Example 1 (English)**:
  > Uniform-Cost Search (UCS): Expands the node with the lowest path cost g(n) from root. Complete and optimal for general non-negative step costs; implemented via priority queue.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ DFS بيوفر جداً في الـ Memory لأن الـ Space complexity بتاعته O(bm)، لكن عيبه إنه مش Optimal وممكن يتعلق في infinite loop لو فيه cycles.

### 303. Informed and Heuristic Search
* **Definition**: Search guided by evaluation functions: Greedy Best-First Search (h(n)), A* Search (f(n) = g(n) + h(n)), heuristic admissibility (h(n) <= h*(n)), consistency (triangle inequality), heuristic dominance.
* **Example 1 (English)**:
  > A* Search Optimality: If heuristic h(n) is admissible (never overestimates true cost) in tree search, or consistent in graph search, A* is guaranteed to return an optimal goal path.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في خوارزمية A* بنحسب f(n) = g(n) + h(n)، بحيث g هي التكلفة الحقيقية من البداية و h هي التكلفة التقريبية المقدرة لحد الهدف، وشرط تكون admissible.

### 304. Adversarial Search and Games
* **Definition**: Competitive multi-agent zero-sum games, game trees, Minimax theorem, Alpha-Beta pruning, static board evaluation functions, depth cutoff, transposition tables.
* **Example 1 (English)**:
  > Alpha-Beta Pruning: Maintains alpha (best choice for MAX so far) and beta (best choice for MIN so far). Subtrees with beta <= alpha are pruned without altering the final minimax decision.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في شجرة الشطرنج الـ Minimax بيفترض إن الخصم بيلعب بأحسن طريقة ممكنة. الـ Alpha-Beta Pruning بيسمح لنا نقطع الفروع اللي مش هتأثر على القرار النهائي عشان نوفر وقت.

### 305. Constraint Satisfaction Problems
* **Definition**: CSP formulation: variables, domains, hard/soft constraints; constraint graphs, Arc Consistency (AC-3), backtracking search with Minimum Remaining Values (MRV) and Forward Checking.
* **Example 1 (English)**:
  > AC-3 Algorithm: Tests every directed arc (X_i, X_j). If value x in domain(X_i) has no allowable match in domain(X_j), remove x from domain(X_i) and propagate revisions to incoming arcs.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في الـ Map Coloring problem كل دولة عبارة عن variable والـ domain هو 3 ألوان، والـ constraint إن مفيش دولتين متجاورتين ياخدوا نفس اللون.

### 306. Propositional and First-Order Logic
* **Definition**: Formal logic: syntax, semantics, truth tables, entailment, validity, satisfiability, Conjunctive Normal Form (CNF), resolution refutation rule, quantifiers (existential, universal), unification.
* **Example 1 (English)**:
  > Resolution Rule: From clauses (A or B) and (not B or C), resolve to infer resolvent (A or C). For proof by refutation, assert Knowledge Base and negate the query, deriving empty clause.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > بنحول كل الجمل في المنطق لـ Conjunctive Normal Form (CNF) عشان نطبق خوارزمية الـ Resolution ونثبت المطلوب بالتناقض.

### 307. Knowledge Representation and Reasoning
* **Definition**: Semantic networks, ontologies, Description Logics, frame-based representations, default reasoning, and expert system inference engines (forward chaining, backward chaining).
* **Example 1 (English)**:
  > Forward Chaining: Data-driven inference starting from known facts in working memory, repeatedly firing matching horn-clause rules to deduce new facts until reaching the query goal.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في الـ Expert Systems، الـ Backward Chaining بيبدأ من الهدف (Goal) ويرجع بالراجع يشوف إيه الحقائق (Facts) اللي محتاجينها عشان نثبت صحته.

### 308. Classical Planning
* **Definition**: Domain planning: states, actions with preconditions and effects, STRIPS, PDDL (Planning Domain Definition Language), forward progression, backward regression, planning graphs.
* **Example 1 (English)**:
  > STRIPS Action Schema: Defined by Action Name, Preconditions (literals that must hold prior to execution), and Effects (literals added or deleted from the state).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في الـ Blocks World problem بنحدد كل حركة للبلوك بشرط (Precondition) زي `Clear(A)` ونتيجة (Effect) زي `On(A, B)`.

### 309. Probabilistic Reasoning and Bayesian Networks
* **Definition**: Probability theory, conditional independence, prior/posterior probabilities, Bayes' Theorem, Directed Acyclic Graph (DAG) Bayesian networks, conditional probability tables (CPTs), d-separation.
* **Example 1 (English)**:
  > Bayesian Network Representation: Nodes represent random variables and directed edges encode direct causal influences. The full joint distribution is factored as product of P(X_i | Parents(X_i)).
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > شبكة بايز (Bayesian Network) بتوفر مساحة تخزين ضخمة للاحتمالات المشتركة عن طريق استغلال الـ Conditional Independence بين المتغيرات.

### 310. Supervised Learning: Regression and Classification
* **Definition**: Supervised learning setup: training/test sets, loss functions (MSE, cross-entropy), linear regression, logistic regression, decision trees (information gain/Gini), k-NN, bias-variance tradeoff.
* **Example 1 (English)**:
  > Logistic Regression: Maps linear combination of inputs w^T x through sigmoid function sigma(z) = 1 / (1 + e^(-z)) to predict class probabilities, optimized via binary cross-entropy loss.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > في الـ Decision Tree بنختار الـ feature اللي بتعمل أعلى Information Gain عشان نقسم الداتا عندها، لحد ما نوصل لـ leaf nodes نقية.

### 311. Unsupervised Learning
* **Definition**: Learning without target labels: K-Means clustering (Lloyd's algorithm, inertia, elbow method), Hierarchical Agglomerative Clustering (linkage criteria), PCA (eigenvectors of covariance matrix).
* **Example 1 (English)**:
  > K-Means Clustering: Alternates between assignment step (assign each sample to closest centroid) and update step (recompute centroid as mean of cluster members) until convergence.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > خوارزمية PCA بنستخدمها في تقليل الأبعاد (Dimensionality Reduction) عن طريق إيجاد الـ Principal Components اللي فيها أكبر تباين (Variance) في الداتا.

### 312. Neural Networks and Deep Learning
* **Definition**: Artificial neurons (perceptrons), activation functions (ReLU, Sigmoid, Softmax), multi-layer perceptron (MLP) architectures, forward pass, backpropagation via chain rule, stochastic gradient descent (SGD).
* **Example 1 (English)**:
  > Backpropagation Algorithm: Computes partial derivatives of the scalar loss with respect to every weight parameter using the chain rule of calculus, enabling gradient descent weight updates.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > الـ ReLU activation function `max(0, x)` بتمنع مشكلة الـ Vanishing Gradient في الـ Deep Neural Networks وبتحسب بسرعة جداً مقارنة بالـ Sigmoid.

### 313. other
* **Definition**: Non-content slides: syllabus breakdown, team project deliverables, Kaggle submission rules, grading scheme, academic integrity pledge, and lecture title/conclusion slides.
* **Example 1 (English)**:
  > CS482 Artificial Intelligence — Spring 2026. Term Project: 20%, Midterm Exam: 20%, Assignments: 20%, Final Exam: 40%. All code must be submitted via GitHub Classroom.
* **Example 2 (Mixed Egyptian Arabic/English)**:
  > تنبيه هام: الغش في بروجكت الذكاء الاصطناعي بيؤدي لرسوب فوري في المادة وتحويل لمجلس تأديب. الكود لازم يكون شغل أصلي لكل تيم.

---

## 6. Inter-Annotator Agreement Protocol

For Issue #28 and ongoing quality assurance:
1. **Blind Annotation Sample**: 200 randomly sampled chunks (stratified across the 3 courses, `seed=42`) are labeled independently by two annotators without viewing each other's labels.
2. **Agreement Metric**: Inter-annotator agreement is evaluated using **Cohen's Kappa ($\kappa$)**:
   $$\kappa = \frac{p_o - p_e}{1 - p_e}$$
3. **Threshold Target**:
   - $\kappa \ge 0.80$: Strong agreement; proceeding with dataset build.
   - $0.65 \le \kappa < 0.80$: Moderate agreement; resolve discrepancies via review meeting.
   - $\kappa < 0.65$: Insufficient consistency; refine labeling definitions and re-annotate.

