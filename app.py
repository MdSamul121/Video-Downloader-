import os
from flask import Flask, request, render_template_string, Response, stream_with_context
import yt_dlp
import requests

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>প্রো ভিডিও ডাউনলোডার</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin-top: 50px; background-color: #f0f2f5; }
        .container { max-width: 500px; margin: auto; padding: 30px; background: white; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
        input[type="text"], select { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; cursor: pointer; background-color: #007bff; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; }
        button:hover { background-color: #0056b3; }
        .footer { margin-top: 20px; font-size: 13px; color: #555; }
        .note { color: #d9534f; font-weight: bold; margin-top: 10px; font-size: 14px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>ভিডিও ডাউনলোডার (Live Progress)</h2>
        <form action="/download" method="post">
            <input type="text" name="url" placeholder="ভিডিওর লিংক দিন..." required>
            <select name="quality">
                <option value="best">Best Quality (সেরা মান)</option>
                <option value="720">720p (HD)</option>
                <option value="480">480p (SD)</option>
                <option value="360">360p (Low)</option>
            </select>
            <button type="submit">ডাউনলোড শুরু করুন</button>
        </form>
        <div class="note">ডাউনলোড শুরু হলে ব্রাউজারের ডাউনলোড সেকশনে প্রোগ্রেস দেখতে পাবেন।</div>
        <div class="footer">সার্ভারে কোনো ফাইল সেভ হয় না, সরাসরি ব্রাউজারে পাঠানো হয়।</div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality')

    if not url:
        return "URL missing", 400

    format_selector = 'best'
    if quality == '720':
        format_selector = 'best[height<=720]'
    elif quality == '480':
        format_selector = 'best[height<=480]'
    elif quality == '360':
        format_selector = 'best[height<=360]'

    ydl_opts = {
        'format': format_selector,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ভিডিওর আসল লিংক এবং ইনফরমেশন বের করা হচ্ছে
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            title = info.get('title', 'video')
            ext = info.get('ext', 'mp4')
            filename = f"{title}.{ext}"

        # আসল ভিডিও সার্ভারে রিকোয়েস্ট পাঠানো হচ্ছে (কিন্তু পুরোটা ডাউনলোড না করে শুধু স্ট্রীম ওপেন করা হচ্ছে)
        r = requests.get(video_url, stream=True)
        
        # ভিডিওর মোট সাইজ (Total Size) বের করা হচ্ছে
        file_size = r.headers.get('Content-Length')

        def generate():
            # ১ মেগাবাইট করে চাঙ্ক পাঠানো হচ্ছে
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    yield chunk

        # রেসপন্স হেডার সেট করা হচ্ছে
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/octet-stream"
        }
        
        # যদি ফাইলের সাইজ পাওয়া যায়, তবে ব্রাউজারকে জানিয়ে দেওয়া হচ্ছে (যাতে সে প্রোগ্রেস বার দেখাতে পারে)
        if file_size:
            headers["Content-Length"] = file_size

        return Response(
            stream_with_context(generate()),
            headers=headers
        )

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
