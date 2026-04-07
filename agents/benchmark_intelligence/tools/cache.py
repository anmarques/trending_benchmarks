"""
Cache Manager for Benchmark Intelligence System

Provides persistent storage for models, benchmarks, documents, and snapshots
using SQLite with content hashing to detect changes.
"""

import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from contextlib import contextmanager

from ..connection_pool import ConnectionPool


class CacheManager:
    """SQLite-backed cache manager for benchmark intelligence data."""

    def __init__(
        self,
        db_path: str = "benchmark_cache.db",
        pool_size: int = 5,
        use_pool: bool = True
    ):
        """
        Initialize the cache manager.

        Args:
            db_path: Path to SQLite database file
            pool_size: Size of connection pool for concurrent access
            use_pool: Whether to use connection pooling (default: True)
        """
        self.db_path = db_path
        self.use_pool = use_pool

        # Initialize connection pool for concurrent access (T012)
        if self.use_pool:
            self._pool = ConnectionPool(
                db_path=db_path,
                pool_size=pool_size,
                timeout=30.0,
                max_retries=3
            )
        else:
            self._pool = None

        self._init_db()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections with automatic retry.

        Uses ConnectionPool for concurrent access with SQLITE_BUSY retry logic.
        Falls back to direct connection if pooling is disabled.
        """
        if self.use_pool and self._pool:
            # Use connection pool with automatic retry (T012)
            with self._pool.connection() as conn:
                yield conn
        else:
            # Direct connection (legacy mode)
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def _init_db(self):
        """Initialize database schema with all tables and indexes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Models table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    lab TEXT,
                    release_date TEXT,
                    first_seen TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    deleted_at TEXT,  -- Timestamp if model deleted from HuggingFace
                    downloads INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    tags TEXT,  -- JSON array
                    model_card_hash TEXT
                )
            """)

            # Benchmarks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_name TEXT UNIQUE NOT NULL,
                    categories TEXT,  -- JSON array
                    attributes TEXT,  -- JSON object
                    first_seen TEXT NOT NULL,
                    last_seen TEXT  -- Track when last mentioned
                )
            """)

            # Model_benchmarks table (many-to-many relationship)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    benchmark_id INTEGER NOT NULL,
                    score REAL,
                    context TEXT,  -- JSON object for shot count, subset, etc.
                    source_type TEXT,  -- model_card, blog, paper, arxiv_paper, github_pdf, etc.
                    source_url TEXT,
                    last_seen TEXT NOT NULL,  -- Track when last mentioned
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id) ON DELETE CASCADE,
                    UNIQUE(model_id, benchmark_id, context)
                )
            """)

            # Documents table (metadata only, no content storage)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id TEXT NOT NULL,
                    doc_type TEXT NOT NULL,  -- model_card, blog, paper, arxiv_paper, github_pdf
                    url TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    extraction_failed BOOLEAN DEFAULT 0,  -- Flag failed extractions to avoid retries
                    last_fetched TEXT NOT NULL,
                    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                    UNIQUE(model_id, doc_type, url)
                )
            """)

            # Snapshots table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    window_start TEXT NOT NULL,
                    window_end TEXT NOT NULL,
                    model_count INTEGER NOT NULL,
                    benchmark_count INTEGER NOT NULL,
                    taxonomy_version TEXT,
                    summary TEXT  -- JSON object with additional stats
                )
            """)

            # Benchmark mentions table (denormalized temporal tracking per snapshot)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_mentions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    benchmark_id INTEGER NOT NULL,
                    absolute_mentions INTEGER NOT NULL,
                    relative_frequency REAL NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    status TEXT NOT NULL,  -- emerging, active, almost_extinct
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE,
                    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id) ON DELETE CASCADE,
                    UNIQUE(snapshot_id, benchmark_id)
                )
            """)

            # Create indexes for better query performance
            # Models indexes (id, lab, last_updated, deleted_at per spec)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_lab
                ON models(lab)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_last_updated
                ON models(last_updated)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_models_deleted
                ON models(deleted_at)
            """)

            # Benchmarks indexes (id, name, category per spec)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmarks_name
                ON benchmarks(canonical_name)
            """)

            # Note: category is stored as JSON TEXT, so we don't index it directly
            # last_seen tracking index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmarks_last_seen
                ON benchmarks(last_seen)
            """)

            # Model_benchmarks indexes (model_id, benchmark_id, source_type, last_seen per spec)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_benchmarks_model
                ON model_benchmarks(model_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_benchmarks_benchmark
                ON model_benchmarks(benchmark_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_benchmarks_source_type
                ON model_benchmarks(source_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_model_benchmarks_last_seen
                ON model_benchmarks(last_seen)
            """)

            # Documents indexes (model_id, content_hash, source_type per spec)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_model
                ON documents(model_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_hash
                ON documents(content_hash)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_source_type
                ON documents(doc_type)
            """)

            # Snapshots indexes (timestamp per spec)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp
                ON snapshots(timestamp)
            """)

            # Benchmark mentions indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmark_mentions_snapshot
                ON benchmark_mentions(snapshot_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmark_mentions_benchmark
                ON benchmark_mentions(benchmark_id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_benchmark_mentions_status
                ON benchmark_mentions(status)
            """)

            # Run migration for existing databases
            self._migrate_schema(cursor)

            conn.commit()

    def _migrate_schema(self, cursor):
        """
        Migrate existing databases to new schema.

        Adds missing columns to existing tables to support new features.
        This is called during _init_db() to ensure backward compatibility.
        """
        # Check if snapshots table needs migration
        cursor.execute("PRAGMA table_info(snapshots)")
        columns = {row[1] for row in cursor.fetchall()}

        # Add missing columns to snapshots table (T005)
        if 'window_start' not in columns:
            cursor.execute("ALTER TABLE snapshots ADD COLUMN window_start TEXT DEFAULT ''")
        if 'window_end' not in columns:
            cursor.execute("ALTER TABLE snapshots ADD COLUMN window_end TEXT DEFAULT ''")
        if 'taxonomy_version' not in columns:
            cursor.execute("ALTER TABLE snapshots ADD COLUMN taxonomy_version TEXT")

        # Note: benchmark_mentions table is created via CREATE TABLE IF NOT EXISTS
        # so no migration needed for new table

    @staticmethod
    def _compute_hash(content: str) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @staticmethod
    def _now() -> str:
        """Get current timestamp in ISO format."""
        return datetime.utcnow().isoformat()

    def add_model(self, model_info: Dict[str, Any]) -> str:
        """
        Add or update a model in the cache.

        Args:
            model_info: Dictionary with model information containing:
                - id: Model identifier (required)
                - name: Model name (required)
                - lab: Lab/organization name
                - release_date: Release date (ISO format)
                - downloads: Download count
                - likes: Like count
                - tags: List of tags
                - model_card: Model card content (for hashing)

        Returns:
            Model ID
        """
        model_id = model_info['id']
        name = model_info['name']
        lab = model_info.get('lab')
        release_date = model_info.get('release_date')
        downloads = model_info.get('downloads', 0)
        likes = model_info.get('likes', 0)
        tags = json.dumps(model_info.get('tags', []))

        # Compute model card hash if provided
        model_card_hash = None
        if 'model_card' in model_info:
            model_card_hash = self._compute_hash(model_info['model_card'])

        now = self._now()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if model exists
            cursor.execute("SELECT id, deleted_at FROM models WHERE id = ?", (model_id,))
            existing = cursor.fetchone()

            if existing:
                # Update existing model (and clear deleted_at if it was deleted before)
                cursor.execute("""
                    UPDATE models
                    SET name = ?, lab = ?, release_date = ?, last_updated = ?,
                        downloads = ?, likes = ?, tags = ?, model_card_hash = ?,
                        deleted_at = NULL
                    WHERE id = ?
                """, (name, lab, release_date, now, downloads, likes, tags,
                      model_card_hash, model_id))
            else:
                # Insert new model
                cursor.execute("""
                    INSERT INTO models
                    (id, name, lab, release_date, first_seen, last_updated,
                     downloads, likes, tags, model_card_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (model_id, name, lab, release_date, now, now,
                      downloads, likes, tags, model_card_hash))

            conn.commit()

        return model_id

    def get_model(self, model_id: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieve model information.

        Args:
            model_id: Model identifier
            include_deleted: If False, return None for deleted models (default: False)

        Returns:
            Dictionary with model information or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if include_deleted:
                cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
            else:
                cursor.execute("SELECT * FROM models WHERE id = ? AND deleted_at IS NULL", (model_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                'id': row['id'],
                'name': row['name'],
                'lab': row['lab'],
                'release_date': row['release_date'],
                'first_seen': row['first_seen'],
                'last_updated': row['last_updated'],
                'deleted_at': row['deleted_at'],
                'downloads': row['downloads'],
                'likes': row['likes'],
                'tags': json.loads(row['tags']) if row['tags'] else [],
                'model_card_hash': row['model_card_hash']
            }

    def add_benchmark(self, name: str, categories: Optional[List[str]] = None,
                     attributes: Optional[Dict[str, Any]] = None) -> int:
        """
        Add or update a benchmark in the cache.

        Args:
            name: Canonical benchmark name
            categories: List of categories (e.g., ["reasoning", "math"])
            attributes: Additional attributes as dictionary

        Returns:
            Benchmark ID
        """
        categories_json = json.dumps(categories or [])
        attributes_json = json.dumps(attributes or {})
        now = self._now()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if benchmark exists
            cursor.execute(
                "SELECT id FROM benchmarks WHERE canonical_name = ?",
                (name,)
            )
            row = cursor.fetchone()

            if row:
                # Update existing benchmark and last_seen timestamp
                benchmark_id = row['id']
                cursor.execute("""
                    UPDATE benchmarks
                    SET categories = ?, attributes = ?, last_seen = ?
                    WHERE id = ?
                """, (categories_json, attributes_json, now, benchmark_id))
            else:
                # Insert new benchmark
                cursor.execute("""
                    INSERT INTO benchmarks
                    (canonical_name, categories, attributes, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, categories_json, attributes_json, now, now))
                benchmark_id = cursor.lastrowid

            conn.commit()

        return benchmark_id

    def get_benchmark(self, benchmark_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve benchmark information.

        Args:
            benchmark_id: Benchmark identifier

        Returns:
            Dictionary with benchmark information or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM benchmarks WHERE id = ?", (benchmark_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                'id': row['id'],
                'canonical_name': row['canonical_name'],
                'categories': json.loads(row['categories']) if row['categories'] else [],
                'attributes': json.loads(row['attributes']) if row['attributes'] else {},
                'first_seen': row['first_seen']
            }

    def get_benchmark_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve benchmark information by canonical name.

        Args:
            name: Canonical benchmark name

        Returns:
            Dictionary with benchmark information or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM benchmarks WHERE canonical_name = ?",
                (name,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return {
                'id': row['id'],
                'canonical_name': row['canonical_name'],
                'categories': json.loads(row['categories']) if row['categories'] else [],
                'attributes': json.loads(row['attributes']) if row['attributes'] else {},
                'first_seen': row['first_seen']
            }

    def add_model_benchmark(self, model_id: str, benchmark_id: int,
                           score: Optional[float] = None,
                           context: Optional[Dict[str, Any]] = None,
                           source_url: Optional[str] = None,
                           source_type: Optional[str] = None) -> int:
        """
        Link a model to a benchmark with score and context.

        Args:
            model_id: Model identifier
            benchmark_id: Benchmark identifier
            score: Benchmark score
            context: Context dict (shot count, subset, etc.)
            source_url: URL of the source
            source_type: Type of source (model_card, arxiv_paper, blog_post, github_pdf, etc.)

        Returns:
            Model-benchmark link ID
        """
        context_json = json.dumps(context or {})
        now = self._now()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Try to update if exists, otherwise insert
            # Update last_seen timestamp on every mention
            cursor.execute("""
                INSERT INTO model_benchmarks
                (model_id, benchmark_id, score, context, source_url, source_type, last_seen, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_id, benchmark_id, context)
                DO UPDATE SET score = ?, source_url = ?, source_type = ?, last_seen = ?, recorded_at = ?
            """, (model_id, benchmark_id, score, context_json, source_url, source_type, now, now,
                  score, source_url, source_type, now, now))

            link_id = cursor.lastrowid
            conn.commit()

        return link_id

    def get_model_benchmarks(self, model_id: str) -> List[Dict[str, Any]]:
        """
        Get all benchmarks for a model.

        Args:
            model_id: Model identifier

        Returns:
            List of benchmark results
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mb.*, b.canonical_name, b.categories, b.attributes
                FROM model_benchmarks mb
                JOIN benchmarks b ON mb.benchmark_id = b.id
                WHERE mb.model_id = ?
                ORDER BY mb.recorded_at DESC
            """, (model_id,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'model_id': row['model_id'],
                    'benchmark_id': row['benchmark_id'],
                    'benchmark_name': row['canonical_name'],
                    'score': row['score'],
                    'context': json.loads(row['context']) if row['context'] else {},
                    'source_url': row['source_url'],
                    'recorded_at': row['recorded_at'],
                    'categories': json.loads(row['categories']) if row['categories'] else [],
                    'attributes': json.loads(row['attributes']) if row['attributes'] else {}
                })

            return results

    def add_document(self, model_id: str, doc_type: str, url: str,
                    content_hash: str, extraction_failed: bool = False) -> int:
        """
        Cache document metadata (hash only, not content per spec).

        Args:
            model_id: Model identifier
            doc_type: Document type (model_card, blog, paper, arxiv_paper, github_pdf)
            url: Document URL
            content_hash: SHA256 hash of document content
            extraction_failed: If True, marks extraction as failed (never retry)

        Returns:
            Document ID
        """
        now = self._now()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Insert or update document metadata (no content storage)
            cursor.execute("""
                INSERT INTO documents
                (model_id, doc_type, url, content_hash, extraction_failed, last_fetched)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(model_id, doc_type, url)
                DO UPDATE SET content_hash = ?, extraction_failed = ?, last_fetched = ?
            """, (model_id, doc_type, url, content_hash, extraction_failed, now,
                  content_hash, extraction_failed, now))

            doc_id = cursor.lastrowid
            conn.commit()

        return doc_id

    def get_document(self, model_id: str, doc_type: str,
                    url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached document.

        Args:
            model_id: Model identifier
            doc_type: Document type
            url: Document URL

        Returns:
            Dictionary with document information or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM documents
                WHERE model_id = ? AND doc_type = ? AND url = ?
            """, (model_id, doc_type, url))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                'id': row['id'],
                'model_id': row['model_id'],
                'doc_type': row['doc_type'],
                'url': row['url'],
                'content_hash': row['content_hash'],
                'extraction_failed': bool(row['extraction_failed']),
                'last_fetched': row['last_fetched']
            }

    def document_changed(self, model_id: str, doc_type: str, url: str,
                        new_content: str) -> bool:
        """
        Check if a document has changed.

        Args:
            model_id: Model identifier
            doc_type: Document type
            url: Document URL
            new_content: New content to compare

        Returns:
            True if document changed or doesn't exist, False otherwise
        """
        new_hash = self._compute_hash(new_content)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content_hash FROM documents
                WHERE model_id = ? AND doc_type = ? AND url = ?
            """, (model_id, doc_type, url))

            row = cursor.fetchone()

            if not row:
                return True  # Document doesn't exist, so it's "changed"

            return row['content_hash'] != new_hash

    def mark_extraction_failed(self, model_id: str, doc_type: str, url: str) -> None:
        """
        Mark a document's extraction as failed (never retry).

        Per SPECIFICATIONS.md Section 2.4: Failed extractions should never be retried,
        preventing infinite retries on permanently broken or irrelevant documents.

        Args:
            model_id: Model identifier
            doc_type: Document type
            url: Document URL
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents
                SET extraction_failed = 1
                WHERE model_id = ? AND doc_type = ? AND url = ?
            """, (model_id, doc_type, url))
            conn.commit()

    def should_skip_extraction(self, model_id: str, doc_type: str, url: str,
                               new_content_hash: str) -> bool:
        """
        Determine if document extraction should be skipped.

        Skip extraction if:
        1. extraction_failed=True (never retry failed extractions - P1-7)
        2. Content hash unchanged and extraction succeeded previously

        Per SPECIFICATIONS.md Section 2.4: Never retry failed extractions.

        Args:
            model_id: Model identifier
            doc_type: Document type
            url: Document URL
            new_content_hash: Hash of new content to compare

        Returns:
            True if extraction should be skipped, False if should proceed
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content_hash, extraction_failed
                FROM documents
                WHERE model_id = ? AND doc_type = ? AND url = ?
            """, (model_id, doc_type, url))

            row = cursor.fetchone()

            if not row:
                # Document doesn't exist, should extract
                return False

            extraction_failed = bool(row['extraction_failed'])
            content_hash = row['content_hash']

            if extraction_failed:
                # Never retry failed extractions (P1-7)
                return True

            # Skip if content hash unchanged (extraction succeeded previously)
            return content_hash == new_content_hash


    def create_snapshot(
        self,
        summary: Optional[Dict[str, Any]] = None,
        window_months: int = 12,
        taxonomy_version: Optional[str] = None
    ) -> int:
        """
        Create a snapshot of the current cache state with rolling window.

        Args:
            summary: Additional summary information as dictionary
            window_months: Number of months for rolling window (default: 12)
            taxonomy_version: Version string of taxonomy used

        Returns:
            Snapshot ID
        """
        now = self._now()
        now_dt = datetime.utcnow()

        # Calculate rolling window boundaries (T008)
        window_end = now_dt.isoformat()
        window_start = (now_dt - timedelta(days=window_months * 30)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get current counts
            cursor.execute("SELECT COUNT(*) as count FROM models")
            model_count = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM benchmarks")
            benchmark_count = cursor.fetchone()['count']

            # Create snapshot with new fields (T008)
            summary_json = json.dumps(summary or {})
            cursor.execute("""
                INSERT INTO snapshots
                (timestamp, window_start, window_end, model_count, benchmark_count, taxonomy_version, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now, window_start, window_end, model_count, benchmark_count, taxonomy_version, summary_json))

            snapshot_id = cursor.lastrowid
            conn.commit()

        return snapshot_id

    def get_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a snapshot.

        Args:
            snapshot_id: Snapshot identifier

        Returns:
            Dictionary with snapshot information or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM snapshots WHERE id = ?", (snapshot_id,))
            row = cursor.fetchone()

            if not row:
                return None

            return {
                'id': row['id'],
                'timestamp': row['timestamp'],
                'model_count': row['model_count'],
                'benchmark_count': row['benchmark_count'],
                'taxonomy_version': row['taxonomy_version'],
                'summary': json.loads(row['summary']) if row['summary'] else {}
            }

    def get_trending_models(self, since_date: str) -> List[Dict[str, Any]]:
        """
        Get models added since a specific date.

        Args:
            since_date: ISO format date string

        Returns:
            List of models added since the date
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM models
                WHERE first_seen >= ?
                ORDER BY first_seen DESC
            """, (since_date,))

            models = []
            for row in cursor.fetchall():
                models.append({
                    'id': row['id'],
                    'name': row['name'],
                    'lab': row['lab'],
                    'release_date': row['release_date'],
                    'first_seen': row['first_seen'],
                    'last_updated': row['last_updated'],
                    'downloads': row['downloads'],
                    'likes': row['likes'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'model_card_hash': row['model_card_hash']
                })

            return models

    def get_benchmark_trends(self) -> List[Dict[str, Any]]:
        """
        Get benchmark popularity trends over time.

        Returns:
            List of benchmarks with usage statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    b.id,
                    b.canonical_name,
                    b.categories,
                    b.attributes,
                    b.first_seen,
                    COUNT(mb.id) as total_models,
                    COUNT(DISTINCT DATE(mb.recorded_at)) as active_days,
                    MIN(mb.recorded_at) as first_recorded,
                    MAX(mb.recorded_at) as last_recorded
                FROM benchmarks b
                LEFT JOIN model_benchmarks mb ON b.id = mb.benchmark_id
                GROUP BY b.id
                ORDER BY total_models DESC
            """)

            trends = []
            for row in cursor.fetchall():
                trends.append({
                    'id': row['id'],
                    'canonical_name': row['canonical_name'],
                    'categories': json.loads(row['categories']) if row['categories'] else [],
                    'attributes': json.loads(row['attributes']) if row['attributes'] else {},
                    'first_seen': row['first_seen'],
                    'total_models': row['total_models'],
                    'active_days': row['active_days'],
                    'first_recorded': row['first_recorded'],
                    'last_recorded': row['last_recorded']
                })

            return trends

    def get_all_models(self) -> List[Dict[str, Any]]:
        """
        Get all models in the cache.

        Returns:
            List of all models
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM models ORDER BY first_seen DESC")

            models = []
            for row in cursor.fetchall():
                models.append({
                    'id': row['id'],
                    'name': row['name'],
                    'lab': row['lab'],
                    'release_date': row['release_date'],
                    'first_seen': row['first_seen'],
                    'last_updated': row['last_updated'],
                    'downloads': row['downloads'],
                    'likes': row['likes'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'model_card_hash': row['model_card_hash']
                })

            return models

    def get_all_benchmarks(self) -> List[Dict[str, Any]]:
        """
        Get all benchmarks in the cache.

        Returns:
            List of all benchmarks
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM benchmarks ORDER BY canonical_name")

            benchmarks = []
            for row in cursor.fetchall():
                benchmarks.append({
                    'id': row['id'],
                    'canonical_name': row['canonical_name'],
                    'categories': json.loads(row['categories']) if row['categories'] else [],
                    'attributes': json.loads(row['attributes']) if row['attributes'] else {},
                    'first_seen': row['first_seen']
                })

            return benchmarks

    def get_recent_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent snapshots.

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            List of recent snapshots
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM snapshots
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            snapshots = []
            for row in cursor.fetchall():
                snapshots.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'model_count': row['model_count'],
                    'benchmark_count': row['benchmark_count'],
                    'summary': json.loads(row['summary']) if row['summary'] else {}
                })

            return snapshots

    def get_models_by_lab(self, lab: str) -> List[Dict[str, Any]]:
        """
        Get all models from a specific lab.

        Args:
            lab: Lab/organization name

        Returns:
            List of models from the lab
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM models
                WHERE lab = ?
                ORDER BY release_date DESC
            """, (lab,))

            models = []
            for row in cursor.fetchall():
                models.append({
                    'id': row['id'],
                    'name': row['name'],
                    'lab': row['lab'],
                    'release_date': row['release_date'],
                    'first_seen': row['first_seen'],
                    'last_updated': row['last_updated'],
                    'downloads': row['downloads'],
                    'likes': row['likes'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'model_card_hash': row['model_card_hash']
                })

            return models

    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model and all associated data.

        Args:
            model_id: Model identifier

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
            deleted = cursor.rowcount > 0
            conn.commit()

        return deleted

    def mark_model_as_deleted(self, model_id: str) -> bool:
        """
        Mark a model as deleted (soft delete) instead of removing it.
        This preserves historical data while excluding from active queries.

        Args:
            model_id: Model identifier

        Returns:
            True if marked as deleted, False if not found
        """
        now = self._now()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE models
                SET deleted_at = ?
                WHERE id = ? AND deleted_at IS NULL
            """, (now, model_id))
            marked = cursor.rowcount > 0
            conn.commit()

        return marked

    def get_all_model_ids(self) -> set:
        """
        Get all model IDs in the cache (including deleted).

        Returns:
            Set of model IDs
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM models")
            return {row['id'] for row in cursor.fetchall()}

    def get_active_model_ids(self) -> set:
        """
        Get all active (non-deleted) model IDs.

        Returns:
            Set of active model IDs
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM models WHERE deleted_at IS NULL")
            return {row['id'] for row in cursor.fetchall()}

    def mark_extraction_failed(self, model_id: str, doc_type: str, url: str) -> bool:
        """
        Mark a document extraction as failed to prevent infinite retries.

        Args:
            model_id: Model identifier
            doc_type: Document type
            url: Document URL

        Returns:
            True if marked, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE documents
                SET extraction_failed = 1
                WHERE model_id = ? AND doc_type = ? AND url = ?
            """, (model_id, doc_type, url))
            marked = cursor.rowcount > 0
            conn.commit()

        return marked

    def should_skip_extraction(self, model_id: str, doc_type: str, url: str,
                               new_hash: str) -> bool:
        """
        Check if extraction should be skipped for a document.

        Extraction is skipped if:
        - extraction_failed=true (never retry failed extractions)
        - hash unchanged and extraction succeeded previously

        Args:
            model_id: Model identifier
            doc_type: Document type
            url: Document URL
            new_hash: New content hash to compare

        Returns:
            True if extraction should be skipped, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT content_hash, extraction_failed FROM documents
                WHERE model_id = ? AND doc_type = ? AND url = ?
            """, (model_id, doc_type, url))

            row = cursor.fetchone()

            if not row:
                return False  # New document, don't skip

            # Skip if extraction failed previously (never retry)
            if row['extraction_failed']:
                return True

            # Skip if hash unchanged (content hasn't changed)
            if row['content_hash'] == new_hash:
                return True

            return False  # Hash changed, need to extract

    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Model stats
            cursor.execute("SELECT COUNT(*) as count FROM models")
            model_count = cursor.fetchone()['count']

            cursor.execute("""
                SELECT COUNT(DISTINCT lab) as count
                FROM models
                WHERE lab IS NOT NULL
            """)
            lab_count = cursor.fetchone()['count']

            # Benchmark stats
            cursor.execute("SELECT COUNT(*) as count FROM benchmarks")
            benchmark_count = cursor.fetchone()['count']

            # Model-benchmark links
            cursor.execute("SELECT COUNT(*) as count FROM model_benchmarks")
            link_count = cursor.fetchone()['count']

            # Document stats
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            document_count = cursor.fetchone()['count']

            cursor.execute("""
                SELECT doc_type, COUNT(*) as count
                FROM documents
                GROUP BY doc_type
            """)
            doc_types = {row['doc_type']: row['count'] for row in cursor.fetchall()}

            # Snapshot stats
            cursor.execute("SELECT COUNT(*) as count FROM snapshots")
            snapshot_count = cursor.fetchone()['count']

            return {
                'models': model_count,
                'labs': lab_count,
                'benchmarks': benchmark_count,
                'model_benchmark_links': link_count,
                'documents': document_count,
                'documents_by_type': doc_types,
                'snapshots': snapshot_count
            }

    def get_benchmarks_within_timeframe(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get benchmarks first seen within the last N months.

        Implements 12-month rolling window for temporal tracking.

        Args:
            months: Number of months to look back (default: 12)

        Returns:
            List of benchmarks within the timeframe
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=months * 30)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM benchmarks
                WHERE first_seen >= ?
                ORDER BY first_seen DESC
            """, (cutoff_date,))

            benchmarks = []
            for row in cursor.fetchall():
                benchmarks.append({
                    'id': row['id'],
                    'canonical_name': row['canonical_name'],
                    'categories': json.loads(row['categories']) if row['categories'] else [],
                    'attributes': json.loads(row['attributes']) if row['attributes'] else {},
                    'first_seen': row['first_seen']
                })

            return benchmarks

    def get_snapshots_within_timeframe(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get snapshots from the last N months.

        Implements 12-month rolling window for temporal tracking.

        Args:
            months: Number of months to look back (default: 12)

        Returns:
            List of snapshots within the timeframe
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=months * 30)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM snapshots
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff_date,))

            snapshots = []
            for row in cursor.fetchall():
                snapshots.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'model_count': row['model_count'],
                    'benchmark_count': row['benchmark_count'],
                    'summary': json.loads(row['summary']) if row['summary'] else {}
                })

            return snapshots

    def get_models_within_timeframe(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get models first seen within the last N months.

        Implements 12-month rolling window for temporal tracking.

        Args:
            months: Number of months to look back (default: 12)

        Returns:
            List of models within the timeframe
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=months * 30)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM models
                WHERE first_seen >= ? AND deleted_at IS NULL
                ORDER BY first_seen DESC
            """, (cutoff_date,))

            models = []
            for row in cursor.fetchall():
                models.append({
                    'id': row['id'],
                    'name': row['name'],
                    'lab': row['lab'],
                    'release_date': row['release_date'],
                    'first_seen': row['first_seen'],
                    'last_updated': row['last_updated'],
                    'downloads': row['downloads'],
                    'likes': row['likes'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'model_card_hash': row['model_card_hash']
                })

            return models

    def get_benchmark_trends_within_timeframe(self, months: int = 12) -> List[Dict[str, Any]]:
        """
        Get benchmark trends within the last N months.

        Filters benchmark popularity data to only include activity from the last N months.

        Args:
            months: Number of months to look back (default: 12)

        Returns:
            List of benchmarks with usage statistics from the timeframe
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=months * 30)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    b.id,
                    b.canonical_name,
                    b.categories,
                    b.attributes,
                    b.first_seen,
                    COUNT(mb.id) as total_models,
                    COUNT(DISTINCT DATE(mb.recorded_at)) as active_days,
                    MIN(mb.recorded_at) as first_recorded,
                    MAX(mb.recorded_at) as last_recorded
                FROM benchmarks b
                LEFT JOIN model_benchmarks mb ON b.id = mb.benchmark_id
                    AND mb.recorded_at >= ?
                GROUP BY b.id
                HAVING COUNT(mb.id) > 0
                ORDER BY total_models DESC
            """, (cutoff_date,))

            trends = []
            for row in cursor.fetchall():
                trends.append({
                    'id': row['id'],
                    'canonical_name': row['canonical_name'],
                    'categories': json.loads(row['categories']) if row['categories'] else [],
                    'attributes': json.loads(row['attributes']) if row['attributes'] else {},
                    'first_seen': row['first_seen'],
                    'total_models': row['total_models'],
                    'active_days': row['active_days'],
                    'first_recorded': row['first_recorded'],
                    'last_recorded': row['last_recorded']
                })

            return trends


    def get_deprecated_benchmarks(self, months: int = 6) -> List[Dict[str, Any]]:
        """
        Get benchmarks not seen in the last N months (potentially deprecated).

        Uses the last_seen timestamp from the benchmarks table to identify
        benchmarks that haven't been mentioned recently.

        Args:
            months: Number of months to look back (default: 6)

        Returns:
            List of potentially deprecated benchmarks with last_seen dates
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=months * 30)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    b.id,
                    b.canonical_name,
                    b.categories,
                    b.attributes,
                    b.first_seen,
                    b.last_seen
                FROM benchmarks b
                WHERE b.last_seen IS NOT NULL
                  AND b.last_seen < ?
                ORDER BY b.last_seen DESC
            """, (cutoff_date,))

            deprecated = []
            for row in cursor.fetchall():
                deprecated.append({
                    'id': row['id'],
                    'canonical_name': row['canonical_name'],
                    'categories': json.loads(row['categories']) if row['categories'] else [],
                    'attributes': json.loads(row['attributes']) if row['attributes'] else {},
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen']
                })

            return deprecated

    @staticmethod
    def classify_benchmark_status(first_seen: str, last_seen: str, window_end: str) -> str:
        """
        Classify benchmark status based on temporal activity.

        Classification rules (T056-T057):
        - emerging: first_seen ≤ 3 months before window_end
        - almost_extinct: last_seen ≥ 9 months before window_end
        - active: all others

        Args:
            first_seen: ISO timestamp when benchmark was first seen
            last_seen: ISO timestamp when benchmark was last seen
            window_end: ISO timestamp for end of rolling window

        Returns:
            Status string: "emerging", "almost_extinct", or "active"
        """
        # Parse timestamps
        first_dt = datetime.fromisoformat(first_seen.replace('Z', '+00:00'))
        last_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
        window_end_dt = datetime.fromisoformat(window_end.replace('Z', '+00:00'))

        # Calculate time differences in days
        days_since_first = (window_end_dt - first_dt).days
        days_since_last = (window_end_dt - last_dt).days

        # Apply classification rules
        # Emerging: first seen ≤ 3 months (90 days) before window end
        if days_since_first <= 90:
            return "emerging"

        # Almost extinct: last seen ≥ 9 months (270 days) before window end
        if days_since_last >= 270:
            return "almost_extinct"

        # Active: everything else
        return "active"

    def create_snapshot_with_window(
        self,
        window_months: int = 12,
        taxonomy_version: Optional[str] = None,
        summary: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create a snapshot with 12-month rolling window and populate benchmark_mentions.

        Implements temporal tracking for Phase 4 (T051-T055, T058):
        - Calculates rolling window boundaries (window_start, window_end)
        - Queries models in window by release_date
        - Computes benchmark statistics (absolute_mentions, relative_frequency)
        - Classifies benchmark status (emerging, active, almost_extinct)
        - Populates benchmark_mentions table with denormalized stats

        Args:
            window_months: Number of months for rolling window (default: 12)
            taxonomy_version: Version string of taxonomy used
            summary: Additional summary information as dictionary

        Returns:
            Snapshot ID
        """
        now = self._now()
        now_dt = datetime.utcnow()

        # Calculate rolling window boundaries (T052)
        window_end = now_dt.isoformat()
        window_start_dt = now_dt - timedelta(days=window_months * 30)
        window_start = window_start_dt.isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Query models in window by release_date (T053)
            # Use release_date if available, otherwise first_seen
            cursor.execute("""
                SELECT id FROM models
                WHERE deleted_at IS NULL
                  AND (
                    (release_date IS NOT NULL AND release_date >= ? AND release_date <= ?)
                    OR
                    (release_date IS NULL AND first_seen >= ? AND first_seen <= ?)
                  )
            """, (window_start, window_end, window_start, window_end))

            models_in_window = {row['id'] for row in cursor.fetchall()}
            model_count = len(models_in_window)

            # Get all benchmarks count
            cursor.execute("SELECT COUNT(*) as count FROM benchmarks")
            benchmark_count = cursor.fetchone()['count']

            # Create snapshot with window boundaries (T051, T052)
            summary_json = json.dumps(summary or {})
            cursor.execute("""
                INSERT INTO snapshots
                (timestamp, window_start, window_end, model_count, benchmark_count, taxonomy_version, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now, window_start, window_end, model_count, benchmark_count, taxonomy_version, summary_json))

            snapshot_id = cursor.lastrowid

            # Compute benchmark statistics for models in window (T054)
            if models_in_window:
                # Build SQL query for models in window
                placeholders = ','.join('?' * len(models_in_window))

                # Get benchmark statistics via SQL aggregation
                cursor.execute(f"""
                    SELECT
                        b.id as benchmark_id,
                        b.canonical_name,
                        b.first_seen,
                        b.last_seen,
                        COUNT(DISTINCT mb.model_id) as absolute_mentions,
                        CAST(COUNT(DISTINCT mb.model_id) AS REAL) / ? as relative_frequency
                    FROM benchmarks b
                    LEFT JOIN model_benchmarks mb ON b.id = mb.benchmark_id
                        AND mb.model_id IN ({placeholders})
                    GROUP BY b.id
                    HAVING absolute_mentions > 0
                """, [model_count] + list(models_in_window))

                benchmark_stats = cursor.fetchall()

                # Populate benchmark_mentions table (T055, T058)
                for stat in benchmark_stats:
                    benchmark_id = stat['benchmark_id']
                    absolute_mentions = stat['absolute_mentions']
                    relative_frequency = stat['relative_frequency']
                    first_seen = stat['first_seen']
                    last_seen = stat['last_seen'] or stat['first_seen']  # Fallback to first_seen

                    # Classify benchmark status (T056-T057)
                    status = self.classify_benchmark_status(first_seen, last_seen, window_end)

                    # Insert into benchmark_mentions
                    cursor.execute("""
                        INSERT INTO benchmark_mentions
                        (snapshot_id, benchmark_id, absolute_mentions, relative_frequency,
                         first_seen, last_seen, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (snapshot_id, benchmark_id, absolute_mentions, relative_frequency,
                          first_seen, last_seen, status))

            conn.commit()

        return snapshot_id

