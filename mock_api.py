"""
API Mock Server Entry Point.

This file serves as a backwards-compatible entry point to run the restructured
modular FastAPI application. It automatically reads environment variables
(such as PORT) to facilitate deployments on hosting services like Render.com.
"""

import os
import uvicorn

if __name__ == "__main__":
    # Render sets the PORT environment variable dynamically
    port = int(os.getenv("PORT", 8000))
    
    # Disable reload on production/Render for performance and stability
    is_render = os.getenv("RENDER") is not None
    reload = not is_render

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
    )
