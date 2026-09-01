# 🚀 CommercePulse - Quick Start Guide

Get CommercePulse running in under 2 minutes!

## ✅ Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.11+ installed (`python --version`)
- ✅ Node.js 20+ installed (`node --version`)
- ✅ Git installed (`git --version`)

---

## 🎯 Step 1: Clone & Navigate

```bash
# Clone the repository
git clone https://github.com/yourusername/commerce-pulse.git

# Navigate to project directory
cd commerce-pulse
```

---

## 🐍 Step 2: Start Backend (Python)

### Windows:
```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install minimal dependencies
pip install fastapi uvicorn pyjwt

# Start the backend server
python simple_server.py
```

### Mac/Linux:
```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install minimal dependencies
pip install fastapi uvicorn pyjwt

# Start the backend server
python simple_server.py
```

**✅ Backend should now be running on http://localhost:8000**

---

## ⚛️ Step 3: Start Frontend (React/Next.js)

Open a **NEW terminal window** and run:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**✅ Frontend should now be running on http://localhost:3000**

---

## 🎉 Step 4: Access the Application

### Open your browser and visit:

**Frontend:** http://localhost:3000
- Landing page with features and pricing
- Login/Register pages
- Dashboard with analytics

**Backend API Docs:** http://localhost:8000/docs
- Interactive API documentation (Swagger UI)
- Test API endpoints directly

---

## 🔐 Step 5: Login

Use the demo account to explore:

```
Email:    demo@commercepulse.com
Password: demo123
```

**Or create a new account:**
1. Go to http://localhost:3000/register
2. Fill in your details
3. Click "Create account"
4. You'll be auto-logged in!

---

## 📊 Step 6: Explore the Dashboard

After logging in, you'll see:

1. **Overview** - Revenue KPIs, charts, customer segments
2. **Sales** - Revenue analytics by channel and category
3. **Customers** - Customer list, segmentation, lifetime value
4. **Products** - Product catalog with inventory tracking
5. **Forecasting** - AI-powered revenue predictions
6. **Anomalies** - Real-time anomaly detection alerts
7. **Data Sources** - Integration management
8. **Settings** - Profile and organization settings

---

## 🛑 Stopping the Servers

### To stop the servers:

**Backend:** Press `Ctrl+C` in the backend terminal

**Frontend:** Press `Ctrl+C` in the frontend terminal

---

## 🔄 Restarting Later

### To restart the servers:

**Backend:**
```bash
cd backend
.\venv\Scripts\Activate.ps1  # Windows
# OR
source venv/bin/activate      # Mac/Linux

python simple_server.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

---

## ⚠️ Common Issues

### Issue 1: "Python not found"
**Solution:** Install Python from https://www.python.org/downloads/

### Issue 2: "Node not found"
**Solution:** Install Node.js from https://nodejs.org/

### Issue 3: Port 8000 already in use
**Solution:** 
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Issue 4: Port 3000 already in use
**Solution:**
```bash
# Run on different port
npm run dev -- -p 3001
```

### Issue 5: "npm install" fails
**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

---

## 📚 What's Next?

### Learn More:
- 📖 Read the full [README.md](README.md)
- 🔧 Check [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for technical details
- 🎨 Explore [FRONTEND_IMPLEMENTATION.md](FRONTEND_IMPLEMENTATION.md) for UI details

### Customize:
- Edit `.env` in backend for configuration
- Edit `.env.local` in frontend for API URL
- Modify `simple_server.py` to add more demo data

### Deploy:
- See deployment guides in `/docs` folder
- Use Docker for containerized deployment
- Deploy frontend to Vercel
- Deploy backend to AWS/Heroku

---

## 🎯 Quick Tips

### Keyboard Shortcuts:
- `Ctrl+C` - Stop server
- `Ctrl+R` - Refresh browser
- `F12` - Open developer console

### Useful Commands:
```bash
# Backend
python simple_server.py --reload  # Auto-reload on changes

# Frontend  
npm run build        # Production build
npm run lint         # Check code quality
npm run typecheck    # Check TypeScript types
```

---

## 💡 Pro Tips

1. **Use Chrome/Firefox** - Best developer experience
2. **Open DevTools** - Press F12 to see network requests
3. **Check Console** - Look for errors in browser console
4. **Watch Terminals** - Keep an eye on backend/frontend logs
5. **Use API Docs** - Test endpoints at http://localhost:8000/docs

---

## 🆘 Need Help?

- **GitHub Issues**: Report bugs or ask questions
- **Email**: support@commercepulse.ai
- **Documentation**: Check `/docs` folder

---

## ✅ Success Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:3000
- [ ] Can access landing page
- [ ] Can login with demo credentials
- [ ] Can see dashboard with data
- [ ] Can navigate between pages
- [ ] Can toggle dark/light theme

---

<div align="center">

**🎉 Congratulations! You're now running CommercePulse!**

**Made with ❤️ by Data Scientists**

[⬆ Back to README](README.md)

</div>
