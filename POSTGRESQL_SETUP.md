# PostgreSQL Database Setup & Enhanced Agent Mode

## 🎯 Overview

This guide covers setting up PostgreSQL database with proper migrations and enhanced Agent mode for the Commit Tracker Service.

## 📋 Prerequisites

1. **PostgreSQL Server** (version 12 or higher)
2. **Python 3.8+** with required packages
3. **Git** for version control

## 🗄️ Database Design

### **Core Tables**

#### **commits** Table
```sql
- id: UUID (Primary Key)
- commit_hash: VARCHAR(40) (Indexed)
- repository_name: VARCHAR(255) (Indexed)
- author_name: VARCHAR(255) (Indexed)
- author_email: VARCHAR(255)
- commit_message: TEXT
- commit_date: TIMESTAMP WITH TIME ZONE (Indexed)
- source_type: ENUM('WEBHOOK', 'LOCAL', 'GIT_SYNC')
- branch_name: VARCHAR(255) (Indexed)
- files_changed: JSON
- lines_added: INTEGER
- lines_deleted: INTEGER
- parent_commits: JSON
- status: ENUM('PENDING', 'PROCESSED', 'FAILED')
- commit_metadata: JSON
- diff_content: TEXT
- file_diffs: JSON
- diff_hash: VARCHAR(64) (Indexed)
- created_at: TIMESTAMP WITH TIME ZONE
- processed_at: TIMESTAMP WITH TIME ZONE
- updated_at: TIMESTAMP WITH TIME ZONE
```

#### **commit_files** Table
```sql
- id: UUID (Primary Key)
- commit_id: UUID (Foreign Key to commits.id)
- filename: VARCHAR(500) (Indexed)
- file_path: VARCHAR(1000)
- file_extension: VARCHAR(20) (Indexed)
- status: VARCHAR(20) (Indexed)
- additions: INTEGER
- deletions: INTEGER
- diff_content: TEXT
- file_size_before: INTEGER
- file_size_after: INTEGER
- language: VARCHAR(50) (Indexed)
- complexity_score: INTEGER
- security_risk_level: VARCHAR(20) (Indexed)
- created_at: TIMESTAMP WITH TIME ZONE
- updated_at: TIMESTAMP WITH TIME ZONE
```

### **Advanced Features**

#### **Full-Text Search**
```sql
-- Generated column for full-text search
search_vector tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('english', coalesce(commit_message, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(author_name, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(repository_name, '')), 'C')
) STORED
```

#### **Materialized View**
```sql
-- Daily commit statistics
CREATE MATERIALIZED VIEW commit_statistics AS
SELECT 
    DATE_TRUNC('day', commit_date) as date,
    COUNT(*) as total_commits,
    COUNT(DISTINCT author_name) as unique_authors,
    SUM(lines_added) as total_lines_added,
    SUM(lines_deleted) as total_lines_deleted,
    AVG(lines_added + lines_deleted) as avg_commit_size
FROM commits
GROUP BY DATE_TRUNC('day', commit_date)
ORDER BY date DESC
```

## 🚀 Setup Instructions

### **1. Install PostgreSQL**

#### **Windows**
```bash
# Download from https://www.postgresql.org/download/windows/
# Or use Chocolatey:
choco install postgresql
```

#### **macOS**
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql
```

#### **Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### **2. Create Database User**

```bash
# Connect to PostgreSQL as superuser
sudo -u postgres psql

# Create user and database
CREATE USER postgres WITH PASSWORD 'password';
CREATE DATABASE commit_tracker OWNER postgres;
GRANT ALL PRIVILEGES ON DATABASE commit_tracker TO postgres;
\q
```

### **3. Install Python Dependencies**

```bash
pip install fastapi uvicorn sqlalchemy asyncpg alembic
```

### **4. Run Database Setup**

```bash
# Run the setup script
python scripts/setup_postgresql.py
```

### **5. Run Migrations**

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Run migrations
alembic upgrade head
```

## 🤖 Enhanced Agent Mode

### **Features**

#### **Productivity Metrics**
- **Productivity Score**: Calculated based on lines added/deleted
- **Commit Patterns**: Feature commits, bug fixes, refactoring
- **Team Collaboration**: Multiple authors analysis
- **Code Quality**: Average commit size, refactoring activity

#### **AI Insights**
- **Excellence Detection**: High productivity recognition
- **Improvement Suggestions**: Low productivity recommendations
- **Growth Analysis**: Feature development vs bug fixing
- **Quality Assessment**: Refactoring activity analysis

#### **Intelligent Recommendations**
- **Pagination**: Large dataset optimization
- **Code Review**: High addition volume alerts
- **Documentation**: Refactoring effort tracking
- **Best Practices**: Commit size optimization

### **API Response Format**

```json
{
  "status": "success",
  "data": {
    "commits": [...],
    "total_count": 14,
    "page": 1,
    "page_size": 10
  },
  "agent": {
    "mode": "enabled",
    "version": "2.0",
    "insights": {
      "analysis": {
        "productivity_metrics": {
          "productivity_score": 85.5,
          "total_lines_added": 1200,
          "total_lines_deleted": 300,
          "net_lines_changed": 900,
          "unique_authors": 3,
          "average_commit_size": 45.2
        },
        "commit_patterns": {
          "feature_commits": 8,
          "bug_fixes": 3,
          "refactor_commits": 2,
          "other_commits": 1
        }
      },
      "recommendations": [
        {
          "type": "excellence",
          "message": "Excellent productivity detected!",
          "priority": "high"
        }
      ],
      "ai_insights": [
        {
          "type": "growth",
          "message": "High feature development activity.",
          "confidence": 0.90
        }
      ]
    },
    "timestamp": "2025-08-29T17:35:00Z"
  }
}
```

## 🧪 Testing

### **Run Comprehensive Tests**

```bash
# Test PostgreSQL setup and Agent mode
python tests/test_postgresql_agent.py
```

### **Test JSON API Conversion**

```bash
# Test GET method
curl -X GET "http://127.0.0.1:8001/api/commits/history/public?limit=10&offset=0&author=mdasif08&branch=main"

# Test POST method (JSON API format)
curl -X POST "http://127.0.0.1:8001/api/commits/history/public" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10, "offset": 0, "author": "mdasif08", "branch": "main"}'
```

## 📊 Performance Optimizations

### **Database Indexes**
- **Primary Keys**: UUID for efficient lookups
- **Search Indexes**: Full-text search with GIN
- **Query Indexes**: Author, date, status for fast filtering
- **Composite Indexes**: Multi-column queries

### **Query Optimization**
- **Pagination**: Efficient LIMIT/OFFSET
- **JSON Queries**: Optimized JSON field access
- **Materialized Views**: Pre-computed statistics
- **Connection Pooling**: AsyncPG for concurrency

### **Caching Strategy**
- **Materialized Views**: Daily statistics
- **Application Cache**: Frequently accessed data
- **Query Result Cache**: Pagination results

## 🔧 Troubleshooting

### **Common Issues**

#### **Connection Failed**
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Check port availability
netstat -an | grep 5432
```

#### **Migration Errors**
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head

# Check migration status
alembic current
alembic history
```

#### **Permission Issues**
```bash
# Fix PostgreSQL permissions
sudo chown -R postgres:postgres /var/lib/postgresql
sudo chmod 700 /var/lib/postgresql/data
```

## 📈 Monitoring

### **Database Metrics**
- **Connection Count**: Active database connections
- **Query Performance**: Slow query analysis
- **Index Usage**: Index efficiency monitoring
- **Storage Growth**: Database size tracking

### **Application Metrics**
- **API Response Time**: Endpoint performance
- **Agent Mode Usage**: AI insights generation
- **Error Rates**: Failed requests tracking
- **User Activity**: API usage patterns

## 🎯 Next Steps

1. **Production Deployment**: Configure production PostgreSQL
2. **Backup Strategy**: Implement automated backups
3. **Monitoring**: Set up database monitoring
4. **Scaling**: Plan for horizontal scaling
5. **Security**: Implement proper authentication

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/)
- [AsyncPG Documentation](https://magicstack.github.io/asyncpg/)
- [FastAPI Database Integration](https://fastapi.tiangolo.com/tutorial/sql-databases/)


