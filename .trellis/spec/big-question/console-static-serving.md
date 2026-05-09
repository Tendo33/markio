# Console Static Serving

The Vue console build is not a separate production server in the default deployment. It builds to `markio/webapp` and FastAPI serves it under `/console`.

Do not change this to a separate frontend deployment or different base path without updating Vite config, FastAPI mount behavior, docs, and tests together.
