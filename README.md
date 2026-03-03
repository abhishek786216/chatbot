# 🏥 Disaster Management RAG Chatbot

An intelligent RAG-enabled chatbot system designed specifically for disaster management, emergency preparedness, and safety protocols. Upload PDFs and train the system with your own disaster management content for accurate, context-aware responses.

## 🌟 Key Features

### 🤖 AI-Powered Responses
- **Groq API Integration**: Uses Llama-3.1-8b-instant model for fast, intelligent responses
- **Disaster Management Focus**: Only responds to emergency and disaster-related topics
- **Conversation Memory**: Maintains context throughout the conversation

### 📚 RAG (Retrieval-Augmented Generation)
- **PDF Document Upload**: Upload emergency manuals, safety guides, disaster plans
- **Intelligent Search**: Keyword-based document retrieval system
- **Context-Aware Answers**: References uploaded documents when answering questions
- **Persistent Knowledge Base**: Documents saved and reusable across sessions

### 👨‍💼 Dual Interface System
- **User Interface** (Port 5001): Clean chat interface for end users
- **Admin Panel** (Port 5001/admin): Upload PDFs, manage content, view statistics

### 🚨 Emergency Features
- **Emergency Contacts**: Store and access critical contact information
- **Location Services**: Manage emergency shelters and important facilities
- **Safety Focused**: All responses prioritize user safety

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Chatbot

**Windows:**
```bash
start.bat
```

**Or manually:**
```bash
python light_rag_chatbot.py
```

### 3. Access the System
- **User Chat**: http://localhost:5001
- **Admin Panel**: http://localhost:5001/admin

## 📖 How to Use

### For Users
1. Open http://localhost:5001 in your browser
2. Start chatting about disaster management topics
3. Ask about emergencies, safety procedures, preparedness, etc.
4. The system will reference uploaded documents for accurate answers

### For Administrators
1. Open http://localhost:5001/admin
2. Upload PDF documents (disaster guides, emergency procedures)
3. System automatically extracts and indexes the content
4. Documents become immediately searchable
5. Add emergency contacts and locations
6. View system statistics

## 🎯 What the Bot Can Help With

The chatbot ONLY responds to disaster management topics:
- ✅ Emergency preparedness and planning
- ✅ Natural disasters (earthquakes, floods, hurricanes, etc.)
- ✅ Emergency response procedures
- ✅ Safety protocols and evacuations
- ✅ First aid and medical emergencies
- ✅ Emergency supplies and equipment
- ✅ Disaster recovery and relief operations

❌ **Non-disaster topics will be politely declined**

## 📁 Project Structure

```
disaster management/
│
├── light_rag_chatbot.py    # Main RAG-enabled application
├── start.bat                # Quick start script (Windows)
├── requirements.txt         # Python dependencies
├── README.md                # This file
│
├── templates/               # HTML templates for web interface
│   ├── user_interface.html
│   └── admin_interface.html
│
├── static/                  # CSS, JavaScript, images
├── uploads/                 # Uploaded PDF storage
├── rag_data/                # RAG system data
└── knowledge_base.json      # Searchable document index
```

## 🔧 System Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- Internet connection (for Groq API)
- 2GB RAM minimum
- Modern web browser

## 📦 Dependencies

Core libraries:
- Flask - Web framework
- Groq - AI model API
- PyMuPDF (fitz) - PDF processing
- Standard Python libraries (json, re, uuid, datetime)

No heavy ML dependencies required! System uses efficient keyword-based search.

## 🔐 Security Note

The API key is embedded in the code for demonstration purposes. For production:
1. Move API key to environment variables
2. Use proper authentication for admin panel
3. Implement file upload size limits
4. Add rate limiting for API calls

## 🎓 Training Your Chatbot

1. Collect disaster management PDFs:
   - Emergency response guides
   - Safety protocols
   - Evacuation procedures
   - First aid manuals
   - Local disaster plans

2. Upload through admin panel (http://localhost:5001/admin)

3. System automatically:
   - Extracts text from PDFs
   - Chunks content intelligently
   - Creates searchable index
   - Makes content available for chat

4. Better PDFs = Smarter responses!

## 🐛 Troubleshooting

**Port Already in Use:**
```bash
# Change port in light_rag_chatbot.py, line 369:
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5001 to another port
```

**PDF Upload Fails:**
- Ensure PDF is readable (not scanned images)
- Check file size (<50MB recommended)
- Verify PDF contains actual text

**Chat Not Responding:**
- Check internet connection
- Verify Groq API key is valid
- Check browser console for errors

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review system logs in terminal
3. Verify all dependencies are installed

## 🎉 Success Indicators

You'll know it's working when:
- ✅ Terminal shows "LIGHT RAG SYSTEM READY!"
- ✅ Can access http://localhost:5001
- ✅ Can upload PDFs in admin panel
- ✅ Chat responds with disaster management info
- ✅ Uploaded documents appear in responses

## 🔄 Version Info

**Current Version**: Light RAG System v1.0
- Lightweight, fast, reliable
- Keyword-based document search
- No heavy ML dependencies
- Production-ready

---

**Built with ❤️ for Emergency Preparedness and Disaster Response**
