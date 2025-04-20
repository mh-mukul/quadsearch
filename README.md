# QuadSearch - Semantic Search Engine

### Summary

QuadSearch is a semantic search engine built using FastAPI, SQLAlchemy, and Qdrant. It provides a simple and efficient way to perform vector-based searches on large datasets. The application is designed to be easily extensible and customizable, allowing developers to build their own search applications on top of it.

Key features:

- Database integration with SQLAlchemy
- Database migrations with Alembic
- Vector search using Qdrant
- Proper logging and error handling
- API endpoint documentation with Swagger UI
- Docker support for easy deployment

Technologies used:

- FastAPI
- SQLAlchemy
- Alembic
- Qdrant
- Docker

### Project Setup

- Create python virtual environment & activate it.
- Install the requirements from requirements.txt by running `pip install -r requirements.txt`.
- Create a .env file from `example.env` and fill up the variables.
- You can select the database of your choice. By default, the application is configured to use SQLite. If you want to use MysQL set `DB_TYPE` to `mysql` and fill up the MYSQL variables.
- Run the application by running `uvicorn app:app --host 0.0.0.0 --port 8001 --reload`. The application server will be running on port 8001 & watch for any changes. Change to your desired port if needed.
- Visit `http://localhost:8001` to verify if the application server has started successfully.
- You can now start building your application on top of this base application.

API Documentation Endpoints(Avaliable only in debug mode):

- `/docs`: Swagger UI documentation for the API endpoints.
- `/redoc`: ReDoc documentation for the API endpoints.

### Qdrant Setup

Qdrant is a vector search engine that can be used for semantic search. To use Qdrant with this application, you need to set up a Qdrant instance. You can either run Qdrant locally using Docker or use a managed Qdrant service.

To run Qdrant locally using Docker, you can use these following commands:

```bash
docker pull qdrant/qdrant
```

```bash
docker run -p 6333:6333 \
    -v $(pwd)/path/to/data:/qdrant/storage \
    qdrant/qdrant
```

This will start a Qdrant instance on port 6333. You can then configure the application to connect to this Qdrant instance by setting the `QDRANT_URL` environment variable in the `.env` file.
You can access the Qdrant API at `http://localhost:6333` and the Qdrant UI at `http://localhost:6333/dashboard`.

Please refer to the official [Qdrant documentation](https://qdrant.tech/documentation/guides/installation/#docker-compose) for more information.

### Database Setup

The application is configured to use SQLite by default. To use a different database, such as MySQL, you will need to update the following environment variables in the `.env` file:

- `DB_TYPE`: Set to `mysql`.
- `DB_HOST`: The hostname or IP address of the database server.
- `DB_PORT`: The port number of the database server.
- `DB_NAME`: The name of the database.
- `DB_USER`: The username for connecting to the database.
- `DB_PASS`: The password for connecting to the database.

After configuring the database connection, you will need to run the database migrations to create the necessary tables. You can do this by running the following command:

```bash
alembic upgrade head
```

### API Endpoints

The following API endpoints are available:

- `/api/v1/create_collection` (POST): Creates a new index in the DB.
- `/api/v1/add_document` (POST): Inserts document rows in a collection.
- `/api/v1/search` (POST): Searches for documents in a collection.

### CLI Commands

The following cli commands are available:

- `python cli.py`:
  - `generate_key`: Generates a new secret key.

### Deployment

The application can be deployed using Docker. Run this following command to build the Docker image and start the container:

```bash
docker-compose up -d --build
```

This will start the application in a detached mode. You can then access the backend at `http://localhost:8001` or the port you specified by DOCKER_PORT in the .env file and Qdrant at `http://localhost:6333`.

To stop the Docker container, run the following command:

```bash
docker-compose down
```

To view the logs of the running container, run the following command:

```bash
docker-compose logs -f
```

To run the database migrations inside the Docker container, you can use the following command:

```bash
docker-compose exec quadsearch-backend alembic upgrade head
```

To run the CLI commands inside the Docker container, you can use the following command:

```bash
docker-compose exec quadsearch-backend python cli.py <command>
```

To browse files inside the Docker container, you can use the following command:

```bash
docker-compose exec quadsearch-backend bash
```
