"""Model C topic classification stub (Issue #23).

Deterministic offline classifier matching chunks against syllabus topics via
normalized TF-IDF and keyword similarity with fallback to 'other'.
"""

import logging
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer

from ml_core.schemas import Chunk, Topic, TopicPrediction
from ml_core.text_normalize import normalize_for_training

LOGGER = logging.getLogger(__name__)

# Topic keyword extensions to enrich vocabulary for syllabus matching
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Arrays and Dynamic Arrays": [
        "array",
        "elements",
        "index",
        "contiguous",
        "resize",
        "capacity",
        "amortized",
    ],
    "Linked Lists": ["pointer", "node", "next", "prev", "head", "tail", "singly", "doubly", "circular"],
    "Stacks and Queues": ["stack", "queue", "lifo", "fifo", "push", "pop", "enqueue", "dequeue", "buffer"],
    "Recursion and Backtracking": [
        "recursion",
        "recursive",
        "base case",
        "call stack",
        "backtracking",
        "recurrence",
    ],
    "Trees and Binary Search Trees": [
        "tree",
        "binary",
        "bst",
        "root",
        "child",
        "left",
        "right",
        "traversal",
        "inorder",
    ],
    "Balanced Trees": ["avl", "rotation", "balance factor", "red-black", "height", "balanced"],
    "Heaps and Priority Queues": ["heap", "priority queue", "min-heap", "max-heap", "heapify", "sift"],
    "Hash Tables and Hashing": ["hash", "bucket", "collision", "chaining", "probing", "load factor", "table"],
    "Graphs and Graph Traversals": [
        "graph",
        "vertex",
        "vertices",
        "edge",
        "adjacency",
        "bfs",
        "dfs",
        "topological",
    ],
    "Shortest Paths and Minimum Spanning Trees": [
        "shortest path",
        "dijkstra",
        "spanning tree",
        "mst",
        "kruskal",
        "prim",
    ],
    "Sorting and Searching Algorithms": ["sort", "merge sort", "quick sort", "binary search", "partition"],
    "Asymptotic Analysis and Big-O": [
        "big-o",
        "complexity",
        "growth rate",
        "asymptotic",
        "worst case",
        "omega",
    ],
    "OS Architecture and System Calls": [
        "kernel",
        "user mode",
        "system call",
        "trap",
        "interrupt",
        "dual mode",
    ],
    "Processes and Process Management": ["process", "pcb", "pid", "fork", "exec", "context switch", "state"],
    "Threads and Concurrency": ["thread", "concurrency", "multithreading", "pthreads", "tcb"],
    "CPU Scheduling Algorithms": [
        "scheduling",
        "round robin",
        "quantum",
        "fcfs",
        "sjf",
        "preemption",
        "scheduler",
    ],
    "Process Synchronization and Mutexes": [
        "critical section",
        "race condition",
        "mutex",
        "synchronization",
        "lock",
    ],
    "Semaphores and Monitors": ["semaphore", "monitor", "wait", "signal", "condition variable"],
    "Deadlocks": ["deadlock", "banker", "safe state", "coffman", "circular wait", "avoidance"],
    "Main Memory Management and Paging": ["paging", "page table", "frame", "tlb", "fragmentation", "memory"],
    "Virtual Memory and Page Replacement": [
        "virtual memory",
        "page fault",
        "replacement",
        "lru",
        "fifo",
        "demand paging",
    ],
    "File System Interface and Implementation": ["file system", "inode", "directory", "block", "journaling"],
    "Mass-Storage and Disk Scheduling": ["disk", "storage", "raid", "ssd", "scan", "sstf", "seek time"],
    "I/O Systems and Device Management": ["io", "device", "dma", "polling", "controller"],
    "Intelligent Agents and Search": ["agent", "peas", "environment", "rational", "sensors", "actuators"],
    "Uninformed Search": ["uninformed", "bfs", "dfs", "uniform cost", "depth-first", "breadth-first"],
    "Informed and Heuristic Search": ["heuristic", "informed", "admissible", "greedy", "evaluation function"],
    "Adversarial Search and Games": ["minimax", "alpha-beta", "pruning", "game", "adversarial", "zero-sum"],
    "Constraint Satisfaction Problems": ["csp", "constraint", "domain", "variable", "arc consistency", "mrv"],
    "Propositional and First-Order Logic": [
        "logic",
        "propositional",
        "first-order",
        "cnf",
        "resolution",
        "inference",
    ],
    "Knowledge Representation and Reasoning": [
        "knowledge",
        "semantic network",
        "ontology",
        "forward chaining",
        "backward chaining",
    ],
    "Classical Planning": ["planning", "strips", "pddl", "action", "precondition", "effect"],
    "Probabilistic Reasoning and Bayesian Networks": [
        "bayesian",
        "probability",
        "bayes",
        "conditional independence",
        "joint",
    ],
    "Supervised Learning: Regression and Classification": [
        "supervised",
        "regression",
        "classification",
        "loss",
        "logistic",
    ],
    "Unsupervised Learning": ["unsupervised", "clustering", "k-means", "pca", "dimensionality"],
    "Neural Networks and Deep Learning": [
        "neural network",
        "deep learning",
        "perceptron",
        "backpropagation",
        "activation",
    ],
    "other": ["syllabus", "grading", "exam", "office hours", "website", "instructor", "rules", "schedule"],
}


def _build_topic_document(topic: Topic) -> str:
    """Enrich topic description with keywords and normalize for TF-IDF matching."""
    extra_keywords = " ".join(TOPIC_KEYWORDS.get(topic.name, []))
    raw_doc = f"{topic.name} {topic.description} {extra_keywords}"
    return normalize_for_training(raw_doc)


def _classify_single_chunk(
    chunk: Chunk,
    candidate_topics: list[Topic],
    vectorizer: TfidfVectorizer,
    topic_matrix: Any,
) -> TopicPrediction:
    """Classify one chunk using TF-IDF cosine similarity against candidate topic vectors."""
    other_topic = next((t for t in candidate_topics if t.name.lower() == "other"), None)
    clean_text = normalize_for_training(chunk.text)

    if not clean_text.strip():
        fallback_id = other_topic.topic_id if other_topic else candidate_topics[0].topic_id
        return TopicPrediction(chunk_id=chunk.chunk_id, topic_id=fallback_id, confidence=0.0)

    chunk_vec = vectorizer.transform([clean_text])
    similarities = (chunk_vec @ topic_matrix.T).toarray()[0]
    best_idx = int(similarities.argmax())
    best_score = float(similarities[best_idx])

    if best_score > 0.05:
        chosen_topic = candidate_topics[best_idx]
        confidence = float(min(1.0, max(0.1, best_score * 1.5)))
    elif other_topic:
        chosen_topic = other_topic
        confidence = 0.5
    else:
        chosen_topic = candidate_topics[best_idx]
        confidence = 0.1

    return TopicPrediction(
        chunk_id=chunk.chunk_id,
        topic_id=chosen_topic.topic_id,
        confidence=round(confidence, 4),
    )


def classify_chunks(chunks: list[Chunk], topics: list[Topic]) -> list[TopicPrediction]:
    """Model C inference contract: classify chunks against syllabus topics.

    Parameters
    ----------
    chunks : list[Chunk]
        Lecture chunks to classify.
    topics : list[Topic]
        Available syllabus topics from course_topics.

    Returns
    -------
    list[TopicPrediction]
        List of predictions matching chunk_id, topic_id, and confidence in [0, 1].
    """
    if not chunks:
        return []
    if not topics:
        raise ValueError("Cannot classify chunks without available topics.")

    # Group candidate topics by course_id for fast scoped filtering
    topics_by_course: dict[int, list[Topic]] = {}
    for t in topics:
        topics_by_course.setdefault(t.course_id, []).append(t)

    # Build TF-IDF representations per course group
    vectorizers: dict[int, tuple[TfidfVectorizer, Any]] = {}
    for course_id, course_topics in topics_by_course.items():
        docs = [_build_topic_document(t) for t in course_topics]
        vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
        mat = vec.fit_transform(docs)
        vectorizers[course_id] = (vec, mat)

    # Classify each chunk
    predictions: list[TopicPrediction] = []
    for chunk in chunks:
        candidate_topics = topics_by_course.get(chunk.course_id) or topics
        vec, mat = vectorizers.get(chunk.course_id, (None, None))
        if vec is None:
            docs = [_build_topic_document(t) for t in candidate_topics]
            vec = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
            mat = vec.fit_transform(docs)

        pred = _classify_single_chunk(chunk, candidate_topics, vec, mat)
        predictions.append(pred)

    return predictions
