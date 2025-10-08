# MyAssistant Setup Guide

## 🚀 Quick Setup

### 1. Get Your OpenAI API Key
1. Go to **https://platform.openai.com/api-keys**
2. Sign in to your OpenAI account
3. Click **"Create new secret key"**
4. Copy the API key (starts with `sk-`)

### 2. Set Up API Key Locally
Create a `.env` file in the project root:
```bash
# Create .env file
echo "OPENAI_API_KEY=your_actual_api_key_here" > .env
```

Replace `your_actual_api_key_here` with your real API key.

### 3. Set Up API Key on Railway (for deployment)
1. Go to **https://railway.app/dashboard**
2. Click on your **MyAssistant project**
3. Go to **"Variables"** tab
4. Click **"New Variable"**
5. Add:
   - **Name:** `OPENAI_API_KEY`
   - **Value:** `your_actual_api_key_here` (paste your real key)
6. Click **"Add"**

### 4. Test Locally
```bash
# Activate virtual environment
source .venv/bin/activate

# Run the app
assistant-web

# Open http://127.0.0.1:8001
```

### 5. Test the Integration
1. **Add some information** by speaking or typing:
   - "My sister's phone number is 555-1234"
   - "I have a meeting tomorrow at 2 PM"

2. **Ask questions** about that information:
   - "What's my sister's number?"
   - "When is my meeting?"

3. **ChatGPT should answer** from your stored memories!

## 🔧 Troubleshooting

### "ChatGPT not available - need API key"
- Make sure you created the `.env` file with your real API key
- Make sure the API key starts with `sk-`
- Restart the app after adding the API key

### "Still not working" on Railway
- Make sure you added the `OPENAI_API_KEY` variable to Railway
- Wait 2-3 minutes for Railway to redeploy
- Check Railway logs for any errors

### Test ChatGPT Integration
Click the **"🤖 Test ChatGPT"** button in the app to test if the API key is working.

## 💡 How It Works

1. **You speak/type** → Your app stores the information
2. **You ask a question** → ChatGPT searches your stored memories
3. **ChatGPT responds** → "Based on what you told me: [your information]"

The app now uses ChatGPT to intelligently answer questions from your stored memories!
