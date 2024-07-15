from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_versioning import VersionedFastAPI, version
from routes.auth import auth_routers
from routes.sessions import sessions_router
from routes.users import users_router
from routes.scrape import scrape_router
from controllers.agent.agentapi import router as agent_router

app = FastAPI()

app = VersionedFastAPI(app, version_format="{major}", prefix_format="/v{major}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
@version(1)
def helth_care():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "ok"})


# app.include_router(api_routers)
app.include_router(auth_routers, tags=["Auth"])

app.include_router(users_router, prefix="/users", tags=["User"])

app.include_router(sessions_router, prefix="/session", tags=["Session"])

app.include_router(scrape_router, prefix="/scrape", tags=["Scrape"])

app.include_router(agent_router)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msgs = [error["msg"] for error in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": error_msgs[0]}  # Return only the first error message
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
