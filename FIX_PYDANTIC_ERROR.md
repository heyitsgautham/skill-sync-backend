# Fix for Pydantic/SQLAlchemy Compatibility Error

## Problem
You're encountering this error:
```
pydantic.errors.PydanticUserError: `TypeAdapter[typing.Annotated[ForwardRef('JoinTransactionMode'), Query(conditional_savepoint)]]` is not fully defined
```

This is a known compatibility issue between:
- FastAPI 0.116.1
- Pydantic 2.10.3
- SQLAlchemy 2.0.23

## Solution

### Option 1: Downgrade SQLAlchemy (Recommended)

1. Stop the backend server (Ctrl+C in the backend terminal)

2. Install the compatible version:
```bash
cd /Users/gauthamkrishna/Projects/presidio/skill-sync/skill-sync-backend
pip install sqlalchemy==1.4.53
```

3. Restart the backend:
```bash
uvicorn app.main:app --reload
```

### Option 2: Upgrade FastAPI (Alternative)

1. Stop the backend server (Ctrl+C)

2. Upgrade FastAPI:
```bash
pip install --upgrade fastapi
```

3. Restart the backend

## Verification

After applying the fix, test the endpoint:

```bash
# Should return 401 Unauthorized (not 500)
curl -X GET "http://localhost:8000/api/resume/my-resumes" -H "Authorization: Bearer test-token"
```

## What Changed

- Updated `requirements.txt` to pin SQLAlchemy to version 1.4.53
- Removed problematic type hints from `connection.py` that confused Pydantic's TypeAdapter
- Added `future=True` flag to sessionmaker for forward compatibility

## Why This Happened

SQLAlchemy 2.0 introduced new parameter types (`JoinTransactionMode`) that FastAPI's dependency injection system couldn't properly validate with Pydantic 2.x. Using SQLAlchemy 1.4.x avoids this issue while still providing all needed functionality.
