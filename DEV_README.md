# Project Setup Guide

This guide will help you set up the virtual environment and install the
necessary dependencies for the project.

## Prerequisites

- Python 3.12 installed on your machine

## Setup Instructions

### Create and Activate the Virtual Environment (optional)

Navigate to the project's root directory. Create a virtual environment
named `.venv` using Python 3.12:

```bash
python3.12 -m venv .venv
```

Activate the virtual environment:

- On Unix or MacOS:

  ```bash
  source .venv/bin/activate
  ```

- On Windows (using Command Prompt):

  ```bash
  .\.venv\Scripts\activate.bat
  ```

### Install Dependencies

With the virtual environment activated, install the project dependencies
using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## Running the Project

With the virtual environment set up and dependencies installed, you're
now ready to run the project according to the project's run
instructions.

## Troubleshooting

If you encounter any issues during the setup, ensure you have the
correct version of Python installed, and the virtual environment is
activated before installing dependencies.
