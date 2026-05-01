from fastapi import FastAPI
app = FastAPI(title="LoanOnboardingAPI")
@app.get("/")
async def root():
    return {"message": "API is up"}
