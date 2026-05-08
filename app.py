import os
from flask import Flask, request, render_template_string, Response, stream_with_context
import yt_dlp
import requests

app = Flask(__name__)

# ইউজার ইন্টারফেস (HTML) - কোয়ালিটি অপশন যুক্ত করা হয়েছে
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
        .footer { margin-top: 20px; font-size: 12px; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h2>ভিডিও ডাউনলোডার (No-Save)</h2>
        <form action="/download" method="post">
            <input type="text" name="url" placeholder="ভিডিওর লিংক দিন (e.g. YouTube, FB...)" required>
            <select name="quality">
                <option value="best">Best Quality (সেরা মান)</option>
                <option value="720">720p (HD)</option>
                <option value="480">480p (SD)</option>
                <option value="360">360p (Low)</option>
            </select>
            <button type="submit">ডাউনলোড শুরু করুন</button>
        </form>
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

    # কোয়ালিটি অনুযায়ী yt-dlp ফরম্যাট নির্ধারণ
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
            # ভিডিওর আসল ডাউনলোড লিংক এবং তথ্য সংগ্রহ করা
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            title = info.get('title', 'video')
            ext = info.get('ext', 'mp4')
            filename = f"{title}.{ext}"

        # সরাসরি ভিডিও সোর্স থেকে স্ট্রিমিং করার ফাংশন
        def generate():
            # রিকোয়েস্ট ছোট ছোট চাঙ্কে (1MB করে) ভিডিওটি নিয়ে আসবে
            with requests.get(video_url, stream=True) as r:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        yield chunk

        # ব্রাউজারকে জানানো হচ্ছে এটি একটি ডাউনলোডযোগ্য ফাইল
        return Response(
            stream_with_context(generate()),
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/octet-stream"
            }
        )

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
