# Deploying SatQuery AI to Render

This guide will help you deploy both the frontend and backend to Render.com (free tier).

## Prerequisites

1. A GitHub account
2. A Render account (sign up at https://render.com)
3. Git installed on your computer

## Step 1: Push to GitHub

First, create a GitHub repository and push your code:

```bash
cd C:\Users\dell\Downloads\satquery-ai-prototype\satquery-ai

# Initialize git (if not already done)
git init

# Add all files
git add .

# Create .gitignore first
echo "backend/venv/" > .gitignore
echo "backend/uploads/" >> .gitignore
echo "frontend/node_modules/" >> .gitignore
echo "frontend/dist/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore

# Add and commit
git add .
git commit -m "Initial commit - SatQuery AI"

# Create a new repository on GitHub (https://github.com/new)
# Name it: satquery-ai

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/satquery-ai.git
git branch -M main
git push -u origin main
```

## Step 2: Deploy Backend to Render

1. Go to https://dashboard.render.com/
2. Click "New +" → "Web Service"
3. Connect your GitHub account if prompted
4. Select your `satquery-ai` repository
5. Configure the service:
   - **Name**: `satquery-backend`
   - **Region**: Oregon (or closest to you)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

6. Add Environment Variable:
   - Click "Advanced" → "Add Environment Variable"
   - Key: `CORS_ORIGINS`
   - Value: `*` (for now, we'll update this later)

7. Click "Create Web Service"

8. Wait for deployment (2-3 minutes). You'll see a URL like:
   ```
   https://satquery-backend.onrender.com
   ```

9. Test the backend by visiting:
   ```
   https://satquery-backend.onrender.com/health
   ```
   You should see: `{"status":"healthy"}`

**Copy the backend URL - you'll need it for the frontend!**

## Step 3: Deploy Frontend to Render

1. Go back to https://dashboard.render.com/
2. Click "New +" → "Static Site"
3. Select the same `satquery-ai` repository
4. Configure the service:
   - **Name**: `satquery-frontend`
   - **Region**: Oregon (same as backend)
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
   - **Instance Type**: `Free`

5. Add Environment Variable:
   - Click "Advanced" → "Add Environment Variable"
   - Key: `VITE_API_URL`
   - Value: `https://satquery-backend.onrender.com` (your backend URL from Step 2)

6. Click "Create Static Site"

7. Wait for deployment (1-2 minutes). You'll get a URL like:
   ```
   https://satquery-frontend.onrender.com
   ```

## Step 4: Update Backend CORS

Now that you have your frontend URL:

1. Go back to your backend service on Render
2. Click "Environment" in the left sidebar
3. Update the `CORS_ORIGINS` variable:
   - Key: `CORS_ORIGINS`
   - Value: `https://satquery-frontend.onrender.com` (your frontend URL)
4. Click "Save Changes"
5. The backend will automatically redeploy

## Step 5: Test Your Deployment

1. Visit your frontend URL:
   ```
   https://satquery-frontend.onrender.com
   ```

2. Upload a test image and try a query

3. Everything should work just like it does locally!

## Troubleshooting

### Backend Issues

**Problem**: Backend shows "Application startup failed"
- Check the logs on Render dashboard
- Make sure all dependencies are in requirements.txt
- Verify Python version is 3.11

**Problem**: CORS errors in browser console
- Update CORS_ORIGINS environment variable with your frontend URL
- Make sure there are no trailing slashes

**Problem**: Image upload fails
- Check that uploads directory is created
- Verify file size limits (Render free tier has limits)

### Frontend Issues

**Problem**: Frontend shows blank page
- Check browser console for errors
- Verify VITE_API_URL is set correctly
- Check that build command succeeded

**Problem**: API calls fail
- Verify backend URL is correct
- Check that backend is running (visit /health endpoint)
- Check CORS settings on backend

**Problem**: Images don't display
- Backend must serve /uploads directory
- Check that image paths are correct

## Free Tier Limitations

Render's free tier has some limitations:
- Services spin down after 15 minutes of inactivity
- First request after spin-down takes 30-60 seconds
- 750 hours per month (shared across all services)
- 100 GB bandwidth per month

For a demo/presentation, this is perfectly fine!

## Alternative: Single Service Deployment

If you want to deploy everything as a single service (simpler but less scalable):

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```

2. Copy the `dist` folder to `backend/static/`

3. Update `backend/app/main.py` to serve static files:
   ```python
   from fastapi.staticfiles import StaticFiles
   
   # Add after other mounts
   app.mount("/", StaticFiles(directory="static", html=True), name="static")
   ```

4. Deploy only the backend service

This gives you a single URL for everything, but the frontend won't auto-update when you push changes.

## Updating Your Deployment

Whenever you make changes:

```bash
git add .
git commit -m "Your changes"
git push
```

Render will automatically redeploy!

## Custom Domain (Optional)

Render supports custom domains:

1. Go to your service settings
2. Click "Custom Domain"
3. Follow the instructions to add your domain
4. Update DNS records

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Render Status: https://status.render.com

## Cost

Both services on free tier = **$0/month**

Perfect for demos, portfolios, and small projects!
