# Analytics Engineering with dbt

This project demonstrates a modern data transformation workflow using **dbt (data build tool)** and **PostgreSQL**. It models an E-commerce schema, transforming raw data into business-ready marts.

## Project Structure
- `seeds/`: Raw CSV data (Customers, Orders).
- `models/staging/`: Initial cleaning and renormalization (Views).
- `models/marts/`: Business logic and aggregation (Tables).
- `docker-compose.yml`: Containerized Postgres and dbt environment.

## How to Run
1. **Start Database**:
   ```bash
   cd dbt_project
   docker-compose up -d postgres
   ```

2. **Run dbt Commands**:
   Run these commands to build the data warehouse:
   
   **Test Connection**:
   ```bash
   docker-compose run dbt debug
   ```
   
   **Load Seed Data (CSV to DB)**:
   ```bash
   docker-compose run dbt seed
   ```
   
   **Run Transformations**:
   ```bash
   docker-compose run dbt run
   ```
   
   **Test Data Quality**:
   ```bash
   docker-compose run dbt test
   ```

3. **Generate Documentation**:
   ```bash
   docker-compose run dbt docs generate
   # To serve docs, you might need port forwarding or local dbt installation
   ```

## Key Concepts Demonstrated
- **ELT**: Loading raw data first (seeds), then transforming.
- **Layered Modeling**: Staging -> Marts.
- **Testing**: Primary keys, referential integrity.
- **Documentaton**: Lineage graphs (via dbt docs).
