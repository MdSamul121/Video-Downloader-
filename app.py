import os
import tempfile
from flask import Flask, request, render_template_string, send_file
import yt_dlp

app = Flask(__name__)

# ইউজার ইন্টারফেস (HTML)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ভিডিও ডাউনলোডার</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f4f4f9; }
        .container { max-width: 500px; margin: auto; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        input[type="text"] { width: 80%; padding: 10px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 5px; }
        button { padding: 10px 20px; cursor: pointer; background-color: #28a745; color: white; border: none; border-radius: 5px; font-size: 16px; }
        button:hover { background-color: #218838; }
    </style>
</head>
<body>
    <div class="container">
        <h2>ভিডিও ডাউনলোডার</h2>
        <p>যেকোনো ভিডিওর লিংক দিন এবং ডাউনলোড করুন</p>
        <form action="/download" method="post">
            <input type="text" name="url" placeholder="এখানে ভিডিওর লিংক দিন..." required>
            <br>
            <button type="submit">ডাউনলোড শুরু করুন</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    # হোমপেজে HTML ফর্ম দেখাবে
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    if not url:
        return "লিংক পাওয়া যায়নি! অনুগ্রহ করে সঠিক লিংক দিন।", 400

    # রেন্ডারের ডিস্কে একটি টেম্পোরারি ফোল্ডার তৈরি করা হচ্ছে
    temp_dir = tempfile.mkdtemp()
    
    ydl_opts = {
        'format': 'best', # সেরা কোয়ালিটি
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'), # সেভ করার লোকেশন
        'noplaylist': True,
        'quiet': True # কনসোলে লগ কম দেখানোর জন্য
    }

    try:
        # yt-dlp দিয়ে ভিডিও ডাউনলোড (এটি RAM এর বদলে ডিস্কে সেভ হবে)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        
        # send_file ফাইলটিকে চাঙ্ক আকারে ইউজারের কাছে পাঠায়, তাই RAM ফুল হয় না
        return send_file(filename, as_attachment=True)
        
    except Exception as e:
        return f"<h3>ডাউনলোড করার সময় সমস্যা হয়েছে!</h3><p>এরর: {str(e)}</p><a href='/'>ফিরে যান</a>", 500

if __name__ == '__main__':
    # রেন্ডার পরিবেশের জন্য পোর্ট কনফিগারেশন
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

