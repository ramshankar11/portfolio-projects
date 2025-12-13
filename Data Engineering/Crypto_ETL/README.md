# Crypto Market Batch ETL

A Python-based ETL pipeline that fetches daily cryptocurrency data, calculates moving averages, and loads it into a PostgreSQL data warehouse. Fully containerized with Docker.

## Project Structure
- `etl_script.py`: Core logic for Extract (API), Transform (Pandas), and Load (SQLAlchemy).
- `Dockerfile`: Defines the Python environment.
- `docker-compose.yml`: Orchestrates the App and Postgres database.

## Prerequisites
- Docker & Docker Compose
- API Key (Optional for CoinGecko free tier)

## How to Run
1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd Crypto_ETL
   ```

2. **Start the pipeline**:
   ```bash
   docker-compose up --build
   ```
   This will:
   - Start a PostgreSQL container.
   - Build the Python image.
   - Run the script to fetch 30 days of standard data.
   - Insert data into the `market_data` table.

3. **Verify Data**:
   Connect to the database:
   ```bash
   docker exec -it <postgres-container-id> psql -U user -d crypto_db
   ```
   Run SQL:
   ```sql
   SELECT * FROM market_data LIMIT 5;
   ```

## Technologies
- **Python 3.9**
- **Pandas**: Data manipulation
- **SQLAlchemy**: ORM/Database connection
- **PostgreSQL**: Data Warehouse
- **Docker**: Containerization
