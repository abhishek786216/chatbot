#!/usr/bin/env python3
"""
Lightweight RAG Chatbot using Basic Text Matching
For Disaster Management - Works without heavy ML dependencies
"""

from flask import Flask, render_template, request, jsonify
from groq import Groq
import os
import json
import fitz  # PyMuPDF
import re
from datetime import datetime
import uuid
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = 'disaster-management-light-rag'

# Configuration
API_KEY = os.environ.get("GROQ_API_KEY", "your_api_key_here")
UPLOAD_FOLDER = 'uploads'
KNOWLEDGE_BASE_FILE = 'knowledge_base.json'

# Initialize
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

try:
    client = Groq(api_key=API_KEY)
    print("✅ Groq API client initialized")
except Exception as e:
    print(f"❌ Error initializing Groq client: {e}")
    client = None

# Simple knowledge base storage
knowledge_base = []
conversations = {}
emergency_contacts = []
query_logs = []  # Store query logs with sources used

def save_query_log(user_message, sources_used, response_preview):
    """Save query log with sources used"""
    global query_logs
    
    query_log = {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'query': user_message,
        'sources_used': sources_used,
        'response_preview': response_preview[:200] + "..." if len(response_preview) > 200 else response_preview,
        'sources_count': len(sources_used)
    }
    
    query_logs.append(query_log)
    
    # Keep only last 100 queries
    if len(query_logs) > 100:
        query_logs = query_logs[-100:]

def load_knowledge_base():
    """Load knowledge base from JSON file"""
    global knowledge_base
    try:
        if os.path.exists(KNOWLEDGE_BASE_FILE):
            with open(KNOWLEDGE_BASE_FILE, 'r', encoding='utf-8') as f:
                knowledge_base = json.load(f)
            print(f"✅ Loaded {len(knowledge_base)} documents from knowledge base")
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        knowledge_base = []

def save_knowledge_base():
    """Save knowledge base to JSON file"""
    try:
        with open(KNOWLEDGE_BASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving knowledge base: {e}")

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def add_to_knowledge_base(text, source_file):
    """Add text to knowledge base with simple chunking"""
    # Simple text chunking - split by paragraphs and sentences
    chunks = []
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        if len(para.strip()) > 50:  # Ignore very short paragraphs
            # Further split long paragraphs
            if len(para) > 1000:
                sentences = re.split(r'[.!?]+', para)
                current_chunk = ""
                for sentence in sentences:
                    if len(current_chunk + sentence) < 800:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
            else:
                chunks.append(para.strip())
    
    # Add chunks to knowledge base
    for i, chunk in enumerate(chunks):
        knowledge_base.append({
            'id': str(uuid.uuid4()),
            'text': chunk,
            'source': source_file,
            'chunk_id': i,
            'timestamp': datetime.now().isoformat()
        })
    
    save_knowledge_base()
    return len(chunks)

def simple_search(query, top_k=3):
    """Simple keyword-based search in knowledge base"""
    if not knowledge_base:
        return []
    
    query_words = set(query.lower().split())
    
    # Score documents based on keyword overlap
    scored_docs = []
    for doc in knowledge_base:
        doc_words = set(doc['text'].lower().split())
        overlap = len(query_words.intersection(doc_words))
        if overlap > 0:
            score = overlap / len(query_words)  # Jaccard-like similarity
            scored_docs.append((score, doc))
    
    # Sort by score and return top k
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    return [doc for score, doc in scored_docs[:top_k]]

def scrape_website(url):
    """Scrape text content from a website"""
    try:
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Set timeout and make request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Filter out very short content
        if len(text) < 100:
            return None, "Website content is too short or unable to extract meaningful text"
        
        return text, None
        
    except requests.exceptions.Timeout:
        return None, "Website request timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return None, f"Failed to access website: {str(e)}"
    except Exception as e:
        return None, f"Error processing website: {str(e)}"

def get_enhanced_response(user_message: str, session_id: str) -> str:
    """Get response using simple RAG + Groq API"""
    try:
        # Search for relevant documents
        relevant_docs = simple_search(user_message, top_k=3)
        
        # Prepare context from retrieved documents
        context = ""
        if relevant_docs:
            context = "Relevant information from knowledge base:\\n"
            for doc in relevant_docs:
                context += f"- {doc['text'][:300]}...\\n"
            context += "\\n"
        
        # Initialize conversation history for new sessions
        if session_id not in conversations:
            conversations[session_id] = []
        
        # Limit conversation history
        if len(conversations[session_id]) > 10:
            conversations[session_id] = conversations[session_id][-10:]
        
        # Create enhanced prompt with context
        system_prompt = """You are a STRICT DISASTER MANAGEMENT knowledge base assistant. 
        You MUST answer user questions ONLY using the provided "Relevant information from knowledge base" context below.
        
        CRITICAL RULES:
        1. If the provided context is empty or does not contain the specific answer to the user's question, you MUST politely reply: "I'm sorry, but I don't have information about that in my specific knowledge base. I can only provide answers based on the uploaded disaster management documents." Do NOT try to invent an answer or use your general internet knowledge.
        2. You ONLY respond to questions strictly related to disaster management. If someone asks about outside topics, politely decline.
        3. You may briefly respond to basic greetings like "hi" or "hello", but immediately remind the user that you are here to answer questions based on your specific disaster database."""
        
        # Prepare messages for API
        messages = [{"role": "system", "content": system_prompt}]
        
        if context:
            messages.append({"role": "system", "content": context})
        
        # Add conversation history
        messages.extend(conversations[session_id])
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get response from Groq
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        
        bot_response = response.choices[0].message.content
        
        # Log query with sources used for admin tracking
        sources_used = []
        if relevant_docs:
            for doc in relevant_docs:
                sources_used.append({
                    'source': doc['source'],
                    'chunk_preview': doc['text'][:100] + "..." if len(doc['text']) > 100 else doc['text'],
                    'chunk_id': doc.get('chunk_id', 0)
                })
        
        save_query_log(user_message, sources_used, bot_response)
        
        # Update conversation history
        conversations[session_id].append({"role": "user", "content": user_message})
        conversations[session_id].append({"role": "assistant", "content": bot_response})
        
        return bot_response
        
    except Exception as e:
        print(f"Error in enhanced response: {e}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again."

@app.route('/')
def index():
    """Main user chat interface"""
    return render_template('user_interface.html')

@app.route('/admin')
def admin():
    """Admin interface for training and management"""
    stats = {
        'total_documents': len(set(doc['source'] for doc in knowledge_base)),
        'total_chunks': len(knowledge_base),
        'storage_used': f"{len(str(knowledge_base)) / 1024:.1f} KB"
    }
    return render_template('admin_interface.html', stats=stats, 
                         emergency_contacts=emergency_contacts)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with RAG enhancement"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data received'}), 400
            
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get enhanced response using light RAG
        bot_response = get_enhanced_response(user_message, session_id)
        
        return jsonify({
            'response': bot_response,
            'success': True
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF upload and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Save uploaded file
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Extract text from PDF
        print(f"Processing PDF: {filename}")
        text = extract_text_from_pdf(filepath)
        
        if not text.strip():
            os.remove(filepath)  # Clean up
            return jsonify({'error': 'No text found in PDF'}), 400
        
        # Add to knowledge base
        chunks_added = add_to_knowledge_base(text, filename)
        
        print(f"Added {chunks_added} chunks from {filename}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {filename}. Added {chunks_added} text chunks to knowledge base.',
            'chunks_added': chunks_added
        })
        
    except Exception as e:
        print(f"PDF upload error: {e}")
        return jsonify({'error': f'Error processing PDF: {str(e)}'}), 500

@app.route('/add_text', methods=['POST'])
def add_text():
    """Handle direct text input for training"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        text_content = data.get('text', '').strip()
        source_name = data.get('source_name', '').strip()
        
        if not text_content:
            return jsonify({'error': 'No text content provided'}), 400
        
        if not source_name:
            source_name = f"Manual_Entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if len(text_content) < 20:
            return jsonify({'error': 'Text content is too short (minimum 20 characters)'}), 400
        
        print(f"Processing text input: {source_name}")
        
        # Add to knowledge base using the same function as PDF
        chunks_added = add_to_knowledge_base(text_content, source_name)
        
        print(f"Added {chunks_added} chunks from text input: {source_name}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed text input "{source_name}". Added {chunks_added} text chunks to knowledge base.',
            'chunks_added': chunks_added,
            'source_name': source_name
        })
        
    except Exception as e:
        print(f"Text input error: {e}")
        return jsonify({'error': f'Error processing text: {str(e)}'}), 500

@app.route('/scrape_website', methods=['POST'])
def scrape_website_route():
    """Handle website scraping and processing"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data received'}), 400
        
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"Scraping website: {url}")
        
        # Scrape the website
        text_content, error = scrape_website(url)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Generate source name from URL
        parsed_url = urlparse(url)
        source_name = f"Website_{parsed_url.netloc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add to knowledge base
        chunks_added = add_to_knowledge_base(text_content, source_name)
        
        print(f"Added {chunks_added} chunks from website: {url}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully scraped and processed website. Added {chunks_added} text chunks to knowledge base.',
            'chunks_added': chunks_added,
            'source_name': source_name,
            'url': url
        })
        
    except Exception as e:
        print(f"Website scraping error: {e}")
        return jsonify({'error': f'Error scraping website: {str(e)}'}), 500

@app.route('/emergency_contacts', methods=['GET', 'POST'])
def manage_emergency_contacts():
    """Manage emergency contacts"""
    global emergency_contacts
    
    if request.method == 'POST':
        try:
            contact = request.get_json()
            emergency_contacts.append({
                'id': str(uuid.uuid4()),
                'name': contact.get('name'),
                'phone': contact.get('phone'),
                'type': contact.get('type'),
                'description': contact.get('description'),
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({'success': True, 'message': 'Contact added successfully'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'contacts': emergency_contacts})

@app.route('/stats')
def get_stats():
    """Get system statistics"""
    stats = {
        'total_documents': len(set(doc['source'] for doc in knowledge_base)),
        'total_chunks': len(knowledge_base),
        'total_contacts': len(emergency_contacts),
        'storage_used': f"{len(str(knowledge_base)) / 1024:.1f} KB",
        'last_update': datetime.now().isoformat()
    }
    return jsonify(stats)

@app.route('/get_stats')
def get_stats_alt():
    """Alternative stats endpoint for compatibility"""
    return get_stats()

@app.route('/clear_database', methods=['POST'])
def clear_database():
    """Clear the knowledge base and reset system"""
    global knowledge_base, emergency_contacts, query_logs
    try:
        # Clear knowledge base, contacts, and query logs
        knowledge_base = []
        emergency_contacts = []
        query_logs = []
        
        # Save empty knowledge base
        save_knowledge_base()
        
        # Remove uploaded files
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                try:
                    os.remove(os.path.join(UPLOAD_FOLDER, filename))
                except:
                    pass
        
        # Remove knowledge base file
        if os.path.exists(KNOWLEDGE_BASE_FILE):
            os.remove(KNOWLEDGE_BASE_FILE)
        
        return jsonify({
            'success': True, 
            'message': 'Database cleared successfully. All documents, contacts, and query logs removed.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error clearing database: {str(e)}'}), 500

@app.route('/view_database')
def view_database():
    """View knowledge base contents for admin"""
    try:
        # Group documents by source
        sources = {}
        for doc in knowledge_base:
            source = doc['source']
            if source not in sources:
                sources[source] = []
            sources[source].append({
                'id': doc['id'],
                'text_preview': doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text'],
                'chunk_id': doc.get('chunk_id', 0),
                'timestamp': doc.get('timestamp', 'Unknown')
            })
        
        return jsonify({
            'success': True,
            'total_sources': len(sources),
            'total_chunks': len(knowledge_base),
            'sources': sources
        })
        
    except Exception as e:
        return jsonify({'error': f'Error viewing database: {str(e)}'}), 500

@app.route('/view_query_logs')
def view_query_logs():
    """View recent queries and sources used"""
    try:
        return jsonify({
            'success': True,
            'total_queries': len(query_logs),
            'query_logs': sorted(query_logs, key=lambda x: x['timestamp'], reverse=True)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error viewing query logs: {str(e)}'}), 500

@app.route('/database_analytics')
def database_analytics():
    """Get analytics about database usage"""
    try:
        # Source usage statistics
        source_usage = {}
        for log in query_logs:
            for source_info in log['sources_used']:
                source = source_info['source']
                if source not in source_usage:
                    source_usage[source] = 0
                source_usage[source] += 1
        
        # Most used sources
        most_used = sorted(source_usage.items(), key=lambda x: x[1], reverse=True)
        
        # Recent query stats
        recent_queries = len([log for log in query_logs if log.get('sources_count', 0) > 0])
        
        analytics = {
            'total_queries': len(query_logs),
            'queries_with_sources': recent_queries,
            'queries_without_sources': len(query_logs) - recent_queries,
            'source_usage': dict(most_used[:10]),  # Top 10 most used sources
            'total_sources_in_db': len(set(doc['source'] for doc in knowledge_base)),
            'total_chunks_in_db': len(knowledge_base)
        }
        
        return jsonify({'success': True, 'analytics': analytics})
        
    except Exception as e:
        return jsonify({'error': f'Error getting analytics: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Starting Light RAG Disaster Management Chatbot...")
    print("Loading knowledge base...")
    load_knowledge_base()
    
    print("✅ LIGHT RAG SYSTEM READY!")
    print("📱 User Interface: http://localhost:5001")
    print("⚙️ Admin Panel: http://localhost:5001/admin")
    print("💡 Features: PDF upload, keyword search, disaster management focus")
    
    app.run(debug=True, host='0.0.0.0', port=5001)