# StitchAI

AI-powered embroidery digitizing SaaS with a Next.js frontend and FastAPI backend.

## Windows Setup Commands

Create the project folder and scaffold directories:

```powershell
mkdir stitch-ai
cd stitch-ai
mkdir frontend, backend, ml
mkdir frontend\app, frontend\components, frontend\lib, frontend\public
mkdir frontend\app\upload, frontend\app\processing, frontend\app\result
mkdir frontend\components\upload, frontend\components\preview, frontend\components\feedback, frontend\components\controls, frontend\components\layout
mkdir backend\routers
mkdir ml\models, ml\training, ml\inference
```

Initialize the frontend:

```powershell
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --no-src-dir
cd ..
```

Install and run the frontend:

```powershell
cd frontend && npm install && npm run dev
```

Install and run the backend:

```powershell
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
```

## API

- `GET /health`
- `POST /api/upload`
- `POST /api/process`
- `GET /api/status/{job_id}`
- `POST /api/feedback`
- `GET /api/feedback/status`
- `GET /api/export/{job_id}/{format}`
- `GET /api/admin/training-report`
