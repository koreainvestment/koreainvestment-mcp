# Generated for koreainvestment-mcp project
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy project definition file
COPY pyproject.toml ./

# Generate requirements.txt from pyproject.toml dependencies
# This step helps ensure dependencies are installed correctly
RUN python -c "import tomllib; deps = tomllib.load(open('pyproject.toml', 'rb'))['project']['dependencies']; print('\n'.join(deps))" > requirements.txt

# Install dependencies using pip from the generated requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code
COPY . /app

# Command to run the application
CMD ["python3", "server.py"]
