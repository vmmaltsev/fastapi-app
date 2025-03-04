# CI/CD Pipeline for FastAPI Application

## Setting Up GitHub Actions

To ensure the correct operation of the CI/CD pipeline, you need to configure the following secrets in your GitHub repository:

1. `DOCKERHUB_USERNAME` - your Docker Hub username
2. `DOCKERHUB_TOKEN` - a Docker Hub access token (not your password!)

### How to Create a Docker Hub Token

1. Log into your Docker Hub account.
2. Go to **"Account Settings"** -> **"Security"**.
3. Click **"New Access Token"**.
4. Enter a description for the token (e.g., **"GitHub Actions"**).
5. Select the necessary permissions (at minimum, **"Read & Write"**).
6. Copy the generated token (it will be shown only once).

### How to Add Secrets to GitHub

1. Navigate to your GitHub repository.
2. Click on the **"Settings"** tab.
3. In the left menu, select **"Secrets and variables"** -> **"Actions"**.
4. Click **"New repository secret"**.
5. Add the secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`.

## What the Pipeline Does

1. **Build and Test**:
   - Builds a Docker image.
   - Runs all tests.
   - Performs a security scan using **Bandit** and **Safety**.
   - Saves the scan results as artifacts.

2. **Publishing**:
   - Runs only on a **push** to the `main` or `master` branches.
   - Builds and pushes the Docker image to **Docker Hub**.
   - Adds tags: branch name, commit short SHA, and `latest`.

## Additional Information

- To run a local security scan:
  ```bash
  pip install bandit safety
  bandit -r app/
  safety check -r requirements.txt

- To manually publish a Docker image:
  ```bash
  docker build -t maltsevvm/fastapi-app:latest .
  docker push maltsevvm/fastapi-app:latest
