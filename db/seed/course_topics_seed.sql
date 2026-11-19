-- Generated from db/seed/course_topics_seed.json (issue #36). Re-run safe: upserts by primary key.
-- Apply after 0001_init.sql. If the JSON changes, regenerate this file in the same PR.

begin;

insert into public.courses (course_id, code, name, name_ar, description) values
    (1, 'ds', 'Data Structures & Algorithms', 'هياكل البيانات والخوارزميات', 'Fundamental linear and non-linear data structures, algorithmic paradigms, and complexity analysis.'),
    (2, 'os', 'Operating Systems', 'نظم التشغيل', 'Operating system concepts, processes, threads, CPU scheduling, concurrency, deadlocks, and memory virtualization.'),
    (3, 'ai', 'Artificial Intelligence & Machine Learning', 'الذكاء الاصطناعي وتعلم الآلة', 'State space search, game playing, constraint satisfaction, logical inference, and foundational machine learning.')
on conflict (course_id) do update set code = excluded.code, name = excluded.name,
    name_ar = excluded.name_ar, description = excluded.description;

insert into public.course_topics (topic_id, course_id, name, description) values
    (101, 1, 'Arrays and Dynamic Arrays', 'Contiguous memory allocation, random access time complexity O(1), amortized resizing analysis, and array manipulations.'),
    (102, 1, 'Linked Lists', 'Singly, doubly, and circular linked lists; pointer manipulation, traversal, insertion, deletion, and cycle detection.'),
    (103, 1, 'Stacks and Queues', 'LIFO/FIFO abstract data types, array and pointer implementations, expression parsing, and priority queue primitives.'),
    (104, 1, 'Recursion and Backtracking', 'Recursive calls, base cases, call stack unwinding, recurrence relations, and depth-first exhaustive search.'),
    (105, 1, 'Trees and Binary Search Trees', 'Hierarchical structures, tree traversals (inorder, preorder, postorder), binary search tree invariant, and node operations.'),
    (106, 1, 'Balanced Trees', 'Self-balancing binary search trees (AVL trees, Red-Black trees), tree rotations, and guaranteed O(log n) height.'),
    (107, 1, 'Heaps and Priority Queues', 'Binary min-heaps and max-heaps, complete binary tree array representation, heapify operations, and heapsort.'),
    (108, 1, 'Hash Tables and Hashing', 'Hash functions, collision resolution mechanisms (chaining, open addressing with linear/quadratic probing), and load factor.'),
    (109, 1, 'Graphs and Graph Traversals', 'Adjacency matrix vs adjacency list, breadth-first search (BFS), depth-first search (DFS), and topological sort.'),
    (110, 1, 'Shortest Paths and Minimum Spanning Trees', 'Dijkstra''s algorithm, Bellman-Ford, Prim''s and Kruskal''s algorithms for minimum spanning trees, and disjoint-set union.'),
    (111, 1, 'Sorting and Searching Algorithms', 'Merge sort, quick sort, binary search, counting sort, radix sort, and lower bound of comparison-based sorting.'),
    (112, 1, 'Asymptotic Analysis and Big-O', 'Growth of functions, Big-O, Big-Omega, Big-Theta notations, time and space complexity, and recurrence master theorem.'),
    (113, 1, 'other', 'Non-content slides: syllabus overview, grading policy, exam schedules, book recommendations, title slides, and logistics.'),
    (201, 2, 'OS Architecture and System Calls', 'Kernel vs user mode, dual-mode operation, system calls, interrupt handling, traps, and OS structures (monolithic vs microkernel).'),
    (202, 2, 'Processes and Process Management', 'Process control block (PCB), process state transitions, context switching, process creation (fork/exec), and IPC mechanisms.'),
    (203, 2, 'Threads and Concurrency', 'User-level vs kernel-level threads, multithreading models (M:1, 1:1, M:N), thread pools, and POSIX pthread programming.'),
    (204, 2, 'CPU Scheduling Algorithms', 'Preemptive vs non-preemptive scheduling, FCFS, SJF, Round Robin, Priority Scheduling, and Multi-Level Feedback Queues.'),
    (205, 2, 'Process Synchronization and Mutexes', 'Critical section problem, race conditions, mutual exclusion conditions, Peterson''s solution, and hardware atomic instructions.'),
    (206, 2, 'Semaphores and Monitors', 'Counting and binary semaphores, wait() and signal() primitives, condition variables, and classic synchronization problems.'),
    (207, 2, 'Deadlocks', 'Four Coffman conditions, resource allocation graphs, deadlock prevention, avoidance with Banker''s algorithm, and detection.'),
    (208, 2, 'Main Memory Management and Paging', 'Contiguous memory allocation, fragmentation (internal/external), paging architecture, page table entries, and TLB caching.'),
    (209, 2, 'Virtual Memory and Page Replacement', 'Demand paging, page faults, Belady''s anomaly, FIFO, Optimal, LRU, Second-chance page replacement, and thrashing.'),
    (210, 2, 'File System Interface and Implementation', 'Directory structures, inodes, file allocation methods (contiguous, linked, indexed), free-space management, and journaling.'),
    (211, 2, 'Mass-Storage and Disk Scheduling', 'Magnetic disks, SSD characteristics, RAID levels, and disk arm scheduling algorithms (FCFS, SSTF, SCAN, C-SCAN, LOOK).'),
    (212, 2, 'I/O Systems and Device Management', 'I/O hardware, polling vs interrupts, direct memory access (DMA), kernel I/O subsystem, blocking vs non-blocking I/O.'),
    (213, 2, 'other', 'Non-content slides: course administration, office hours, grading rubric, lab submission guidelines, and title slides.'),
    (301, 3, 'Intelligent Agents and Search', 'Rational agents, PEAS framework, environment types (deterministic, observable), state-space representations, and goal formulations.'),
    (302, 3, 'Uninformed Search', 'Breadth-First Search (BFS), Depth-First Search (DFS), Uniform-Cost Search (UCS), and iterative deepening depth-first search.'),
    (303, 3, 'Informed and Heuristic Search', 'Greedy Best-First Search, A* search, admissible and consistent heuristics, dominance, and heuristic evaluation functions.'),
    (304, 3, 'Adversarial Search and Games', 'Zero-sum two-player games, Minimax theorem, alpha-beta pruning optimization, evaluation functions, and horizon effect.'),
    (305, 3, 'Constraint Satisfaction Problems', 'Variables, domains, and constraints; constraint propagation with AC-3, backtracking search with MRV and forward checking.'),
    (306, 3, 'Propositional and First-Order Logic', 'Syntax and semantics of propositional and predicate logic, CNF conversion, resolution inference rule, and unification.'),
    (307, 3, 'Knowledge Representation and Reasoning', 'Ontologies, semantic networks, frame systems, default reasoning, and rule-based expert systems.'),
    (308, 3, 'Classical Planning', 'STRIPS and PDDL representations, forward state-space search, backward goal-stack planning, and planning graphs.'),
    (309, 3, 'Probabilistic Reasoning and Bayesian Networks', 'Conditional independence, Bayes rule, joint probability distributions, Bayesian network topologies, and d-separation.'),
    (310, 3, 'Supervised Learning: Regression and Classification', 'Linear and logistic regression, decision trees, k-nearest neighbors, naive Bayes, loss functions, and cross-validation.'),
    (311, 3, 'Unsupervised Learning', 'K-means clustering, hierarchical agglomerative clustering, Gaussian mixture models, and principal component analysis (PCA).'),
    (312, 3, 'Neural Networks and Deep Learning', 'Perceptrons, multi-layer feedforward networks, activation functions, backpropagation via gradient descent, and loss landscapes.'),
    (313, 3, 'other', 'Non-content slides: instructor contacts, academic honesty policy, grading scheme, term project logistics, and title slides.')
on conflict (topic_id) do update set course_id = excluded.course_id, name = excluded.name,
    description = excluded.description;

commit;
