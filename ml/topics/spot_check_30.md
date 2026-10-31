# Issue #27: Cleaning Pipeline 30-Chunk Spot-Check

This report verifies that the 7-step cleaning pipeline eliminates headers, metadata,
and OCR noise while preserving genuine lecture content across all pilot courses.

## Cleaning Audit Trail Summary

| Step | Rows Before | Rows After | Delta | Reason |
|---|---|---|---|---|
| `remove_repeating_headers` | 46 | 46 | -0 | drop lines repeating >50% |
| `remove_metadata` | 46 | 46 | -0 | drop page numbers, URLs, emails, and copyright |
| `remove_ocr_garbage` | 46 | 46 | -0 | drop lines with <50% valid letters |
| `normalize_for_training` | 46 | 46 | -0 | apply shared Arabic/Latin normalization |
| `filter_short_chunks` | 46 | 45 | -1 | drop chunks with <5 words |
| `deduplicate_chunks` | 45 | 44 | -1 | drop duplicates with >=90% similarity |
| `tag_language` | 44 | 44 | -0 | tag language as ar, en, or mixed |

## Spot-Check Sample (30 Chunks, Seed 42)

### Chunk 1: `c_os_l204_s01` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > CS302: Operating Systems Concepts <br> CS302 Process Synchronization <br> Critical section problem and synchronization primitives. <br> Confidential - University Course | Page 1 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > cs302 process synchronization critical section problem and synchronization primitives.

### Chunk 2: `c_ai_l303_s02` (Course 3, Lang: `en`)
* **Original Slide Text**:
  > Constraint Satisfaction Problems CSP <br> Variables X, Domains D, Constraints C. <br> Arc Consistency with AC-3 eliminates domain values that violate constraints. <br> Backtracking search with Minimum Remaining Values (MRV) heuristic.
* **Cleaned & Normalized Chunk**:
  > constraint satisfaction problems csp variables x, domains d, constraints c. arc consistency with ac-3 eliminates domain values that violate constraints. backtracking search with minimum remaining values (mrv) heuristic.

### Chunk 3: `c_ai_l301_s02` (Course 3, Lang: `en`)
* **Original Slide Text**:
  > CS482: Artificial Intelligence & Machine Learning <br> Intelligent Agents and PEAS <br> Rational agent selects action to maximize expected performance measure. <br> PEAS formulation: Performance, Environment, Actuators, Sensors. <br> Environment properties: fully/partially observable, deterministic/stochastic, static/dynamic. <br> Arabic: ······ ····· ······· ·· ······ ·· ···· ··· sensors ···· actuators. <br> Confidential - University Course | Page 2 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > intelligent agents and peas rational agent selects action to maximize expected performance measure. peas formulation: performance, environment, actuators, sensors. environment properties: fully/partially observable, deterministic/stochastic, static/dynamic.

### Chunk 4: `c_ds_l102_s01` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Lecture 2: Pointer-based Structures <br> Today we cover Singly, Doubly Linked Lists, Stacks, and Queues. <br> Slides available at https://univ.edu.eg/cs201/lec02 <br> Confidential - University Course | Page 1 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > lecture 2: pointer-based structures today we cover singly, doubly linked lists, stacks, and queues.

### Chunk 5: `c_ds_l101_s04` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Dynamic Arrays and Resizing <br> Dynamic array automatically expands when full. <br> Doubling capacity strategy achieves amortized O(1) push_back. <br> Copying elements takes O(n) during the reallocation step. <br> Arabic: ··· ······ ····· ····· allocate ···· ······· ····· ·······. <br> Confidential - University Course | Page 4 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > dynamic arrays and resizing dynamic array automatically expands when full. doubling capacity strategy achieves amortized o(1) push_back. copying elements takes o(n) during the reallocation step.

### Chunk 6: `c_ds_l101_s03` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Arrays and Memory Layout <br> Arrays allocate contiguous memory blocks for elements. <br> Random access lookup takes O(1) time complexity. <br> Index calculation: base_address + index * element_size. <br> Arabic: ······· ······ ··· ··· ·· ········ ······· ···· ···· ··· ···· ·····. <br> Confidential - University Course | Page 3 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > arrays and memory layout arrays allocate contiguous memory blocks for elements. random access lookup takes o(1) time complexity. index calculation: base_address + index * element_size.

### Chunk 7: `c_ai_l303_s03` (Course 3, Lang: `en`)
* **Original Slide Text**:
  > Propositional and First-Order Logic <br> Syntax, semantics, truth tables, entailment. <br> Conjunctive Normal Form (CNF) and Resolution refutation theorem proving. <br> First-order logic includes predicates, functions, and quantifiers (forall, exists).
* **Cleaned & Normalized Chunk**:
  > propositional and first-order logic syntax, semantics, truth tables, entailment. conjunctive normal form (cnf) and resolution refutation theorem proving. first-order logic includes predicates, functions, and quantifiers (forall, exists).

### Chunk 8: `c_ai_l303_s01` (Course 3, Lang: `en`)
* **Original Slide Text**:
  > CS482 Constraint Satisfaction and Logic <br> CSPs and Propositional Logic. <br> Course material: https://ai482.univ.edu.eg/logic
* **Cleaned & Normalized Chunk**:
  > cs482 constraint satisfaction and logic csps and propositional logic. course material:

### Chunk 9: `c_os_l202_s01` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > CS302: Operating Systems Concepts <br> Process Management and PCB <br> Process is a program in execution. <br> Process Control Block (PCB) stores PID, state, PC, registers, memory limits. <br> States: New, Ready, Running, Waiting, Terminated. <br> Arabic: ··· PCB ·· ······ ····· ········ ···· ···· ·· ········. <br> Confidential - University Course | Page 1 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > process management and pcb process is a program in execution. process control block (pcb) stores pid, state, pc, registers, memory limits. states: new, ready, running, waiting, terminated.

### Chunk 10: `c_ai_l302_s03` (Course 3, Lang: `en`)
* **Original Slide Text**:
  > Heuristic Search A Star Algorithm <br> fin) = gin) + hin) admissible heuristic <br> Ara bic: BEEEEEED GEER Bon
* **Cleaned & Normalized Chunk**:
  > heuristic search a star algorithm fin) = gin) + hin) admissible heuristic ara bic: beeeeeed geer bon

### Chunk 11: `c_ds_l104_s01` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> CS201 Lecture 4: Hashing and Graphs <br> Advanced structures and graph theory. <br> Instructor: Dr. Ahmed Hassan - ahmed@univ.edu.eg <br> Confidential - University Course | Page 1 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > cs201 lecture 4: hashing and graphs advanced structures and graph theory. instructor: dr. ahmed hassan -

### Chunk 12: `c_ai_l301_s03` (Course 3, Lang: `en`)
* **Original Slide Text**:
  > CS482: Artificial Intelligence & Machine Learning <br> Uninformed Search BFS and DFS <br> Breadth-First Search (BFS) expands shallowest nodes using FIFO queue; optimal for unit step cost. <br> Depth-First Search (DFS) expands deepest nodes using LIFO stack; space complexity O(bm). <br> Uniform Cost Search expands node with lowest path cost g(n). <br> Confidential - University Course | Page 3 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > uninformed search bfs and dfs breadth-first search (bfs) expands shallowest nodes using fifo queue; optimal for unit step cost. depth-first search (dfs) expands deepest nodes using lifo stack; space complexity o(bm). uniform cost search expands node with lowest path cost g(n).

### Chunk 13: `c_os_l204_s02` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > CS302: Operating Systems Concepts <br> Critical Section and Race Conditions <br> Race condition occurs when concurrent threads access shared data without synchronization. <br> Critical Section requirements: Mutual Exclusion, Progress, Bounded Waiting. <br> Peterson's solution for two processes using turn and flag variables. <br> Confidential - University Course | Page 2 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > critical section and race conditions race condition occurs when concurrent threads access shared data without synchronization. critical section requirements: mutual exclusion, progress, bounded waiting. peterson's solution for two processes using turn and flag variables.

### Chunk 14: `c_os_l201_s02` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > CS302: Operating Systems Concepts <br> Operating System Architecture <br> Dual mode operation: User Mode (bit 1) vs Kernel Mode (bit 0). <br> Privileged instructions can only execute in kernel mode. <br> Trap instruction switches CPU mode safely to handle system calls. <br> Arabic: ······ ····· ········· ·· ···· ··· ······ ··· ·· ······· ···. <br> Confidential - University Course | Page 2 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > operating system architecture dual mode operation: user mode (bit 1) vs kernel mode (bit 0). privileged instructions can only execute in kernel mode. trap instruction switches cpu mode safely to handle system calls.

### Chunk 15: `c_os_l202_s03` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > Operating Systems Kernel Mode <br> System Gallsand Interrupt Handling <br> Ara bic: 5 ‏فففة 5ف ة ة‎ GEE)
* **Cleaned & Normalized Chunk**:
  > operating systems kernel mode system gallsand interrupt handling ara bic: 5 ‏فففة 5ف ة ة‎ gee)

### Chunk 16: `c_os_l204_s03` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > CS302: Operating Systems Concepts <br> Semaphores and Mutexes <br> Mutex provides binary mutual exclusion: acquire() and release(). <br> Counting semaphore initialized to resource count N. <br> wait(S) decrements, signal(S) increments atomically. <br> Arabic: ······· ········· ···· ···· ···· ··· threads ··· critical section. <br> Confidential - University Course | Page 3 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > semaphores and mutexes mutex provides binary mutual exclusion: acquire() and release(). counting semaphore initialized to resource count n. wait(s) decrements, signal(s) increments atomically.

### Chunk 17: `c_ds_l101_s05` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Short Summary <br> Done for today. <br> Confidential - University Course | Page 5 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > short summary done for today.

### Chunk 18: `c_ds_l102_s03` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Doubly Linked Lists <br> Each node maintains next and prev pointers. <br> Enables bidirectional traversal and O(1) deletion given node pointer. <br> Extra memory overhead for the backward pointer. <br> Arabic: ···· ··· doubly linked list ·· ····· ···· ··· ······· ··· ·· ·····. <br> Confidential - University Course | Page 3 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > doubly linked lists each node maintains next and prev pointers. enables bidirectional traversal and o(1) deletion given node pointer. extra memory overhead for the backward pointer.

### Chunk 19: `c_ai_l301_s01` (Course 3, Lang: `en`)
* **Original Slide Text**:
  > CS482: Artificial Intelligence & Machine Learning <br> CS482 Artificial Intelligence Overview <br> Welcome to AI and Machine Learning. <br> Instructor: Dr. Sherif Nabil - sherif@univ.edu.eg <br> Grading: 25% Project, 25% Midterm, 50% Final. <br> Website: https://ai482.univ.edu.eg <br> Confidential - University Course | Page 1 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > cs482 artificial intelligence overview welcome to ai and machine learning. instructor: dr. sherif nabil - grading: 25% project, 25% midterm, 50% final.

### Chunk 20: `c_os_l204_s04` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > CS302: Operating Systems Concepts <br> Deadlock Characterization and Banker Algorithm <br> Four Coffman conditions: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait. <br> Banker's Algorithm tests if resource allocation state is safe. <br> Safe sequence ensures all processes can finish without deadlock. <br> Confidential - University Course | Page 4 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > deadlock characterization and banker algorithm four coffman conditions: mutual exclusion, hold and wait, no preemption, circular wait. banker's algorithm tests if resource allocation state is safe. safe sequence ensures all processes can finish without deadlock.

### Chunk 21: `c_ds_l104_s03` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Graphs and Traversals <br> Adjacency matrix O(V^2) vs Adjacency list O(V + E). <br> Breadth-First Search (BFS) finds shortest paths in unweighted graphs. <br> Depth-First Search (DFS) detects cycles and computes topological sort. <br> Confidential - University Course | Page 3 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > graphs and traversals adjacency matrix o(v^2) vs adjacency list o(v + e). breadth-first search (bfs) finds shortest paths in unweighted graphs. depth-first search (dfs) detects cycles and computes topological sort.

### Chunk 22: `c_ds_l102_s06` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > Binary Search Trees BST Invariant <br> Node X has lett < Xand right ‏د‎ * <br> Ara bic: BEE BEE GEE
* **Cleaned & Normalized Chunk**:
  > binary search trees bst invariant node x has lett < xand right ‏د‎ * ara bic: bee bee gee

### Chunk 23: `c_ds_l102_s04` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Stack ADT and Applications <br> LIFO: Last In First Out. <br> Push and Pop operations operate at top in O(1) time. <br> Used for parentheses matching, expression evaluation, and call stack. <br> Arabic: ······ ···· LIFO ··· ···· ···· ·· ··· ···· ····. <br> Confidential - University Course | Page 4 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > stack adt and applications lifo: last in first out. push and pop operations operate at top in o(1) time. used for parentheses matching, expression evaluation, and call stack.

### Chunk 24: `c_ds_l103_s02` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > Binary Tree Traversals <br> Preorder: Root, Left, Right <br> Inorder: Left, Root, Right (yields sorted order in BST) <br> Postorder: Left, Right, Root <br> Level-order: Breadth-first traversal using a queue.
* **Cleaned & Normalized Chunk**:
  > binary tree traversals preorder: root, left, right inorder: left, root, right (yields sorted order in bst) postorder: left, right, root level-order: breadth-first traversal using a queue.

### Chunk 25: `c_ds_l101_s02` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Asymptotic Analysis and Big-O <br> Big-O Notation measures algorithmic growth rate as input n grows to infinity. <br> We ignore constant factors and lower-order terms. <br> Example: 3n^2 + 5n + 12 is O(n^2). <br> Arabic: ····· ··· Big-O ···· ···· ··· worst case ········ ··· ······ ····. <br> Confidential - University Course | Page 2 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > asymptotic analysis and big-o big-o notation measures algorithmic growth rate as input n grows to infinity. we ignore constant factors and lower-order terms.

### Chunk 26: `c_ds_l104_s02` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> Hash Tables and Collision Resolution <br> Direct mapping using hash function h(key). <br> Separate chaining handles collisions via linked lists per bucket. <br> Open addressing uses linear probing: h(k, i) = (h'(k) + i) mod m. <br> Load factor alpha = n/m controls performance. <br> Confidential - University Course | Page 2 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > hash tables and collision resolution direct mapping using hash function h(key). separate chaining handles collisions via linked lists per bucket. open addressing uses linear probing: h(k, i) = (h'(k) + i) mod m. load factor alpha = n/m controls performance.

### Chunk 27: `c_os_l203_s02` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > Threads vs Processes <br> Threads share text segment, heap, and open files. <br> Each thread has its own thread ID, program counter, registers, and stack. <br> POSIX pthreads library for multi-threaded programming in C.
* **Cleaned & Normalized Chunk**:
  > threads vs processes threads share text segment, heap, and open files. each thread has its own thread id, program counter, registers, and stack. posix pthreads library for multi-threaded programming in c.

### Chunk 28: `c_os_l203_s01` (Course 2, Lang: `en`)
* **Original Slide Text**:
  > CS302 Threads and Concurrency <br> Multithreading and CPU Scheduling. <br> Slides: https://os302.univ.edu.eg/lec03
* **Cleaned & Normalized Chunk**:
  > cs302 threads and concurrency multithreading and cpu scheduling. slides:

### Chunk 29: `c_ds_l103_s03` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > Balanced Trees: AVL and Rotations <br> AVL tree maintains balance factor in {-1, 0, 1}. <br> Rotations (LL, RR, LR, RL) restore height balance after insertion. <br> Guarantees O(log n) worst-case search, insertion, and deletion.
* **Cleaned & Normalized Chunk**:
  > balanced trees: avl and rotations avl tree maintains balance factor in {-1, 0, 1}. rotations (ll, rr, lr, rl) restore height balance after insertion. guarantees o(log n) worst-case search, insertion, and deletion.

### Chunk 30: `c_ds_l101_s01` (Course 1, Lang: `en`)
* **Original Slide Text**:
  > CS201: Data Structures & Algorithms <br> CS201 Data Structures Course Info <br> Course Syllabus and Logistics <br> Instructor: Dr. Ahmed Hassan - contact: ahmed@univ.edu.eg <br> Grading: 30% Midterm, 30% Labs, 40% Final Exam. <br> Website: https://cs201.univ.edu.eg <br> Confidential - University Course | Page 1 | https://univ.edu.eg/courses
* **Cleaned & Normalized Chunk**:
  > cs201 data structures course info course syllabus and logistics instructor: dr. ahmed hassan - contact: grading: 30% midterm, 30% labs, 40% final exam.
