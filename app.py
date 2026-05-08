import os
from flask import Flask, request, render_template, send_from_directory, Response, stream_with_context
import yt_dlp
import requests

# Flask কে dist ফোল্ডার চিনিয়ে দেওয়া হলো
app = Flask(__name__, static_folder='dist/assets', template_folder='dist')

# হোমপেজে React এর index.html দেখাবে
@app.route('/')
def index():
    return render_template('index.html')

# React এর অন্যান্য স্ট্যাটিক ফাইল (যেমন আইকন বা ছবি) লোড করার জন্য
@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join('dist', path)):
        return send_from_directory('dist', path)
    return render_template('index.html')

# ভিডিও ডাউনলোড করার API
@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    quality = request.form.get('quality')

    if not url:
        return "URL missing", 400

    format_selector = 'best'
    if quality == '720':
        format_selector = 'best[height<=720]/best'
    elif quality == '480':
        format_selector = 'best[height<=480]/best'
    elif quality == '360':
        format_selector = 'best[height<=360]/best'

    ydl_opts = {
        'format': format_selector,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_url = info.get('url')
            title = info.get('title', 'video')
            ext = info.get('ext', 'mp4')
            filename = f"{title}.{ext}"

        r = requests.get(video_url, stream=True)
        file_size = r.headers.get('Content-Length')

        def generate():
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    yield chunk

        headers = {
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Type": "application/octet-stream"
        }
        
        if file_size:
            headers["Content-Length"] = file_size

        return Response(stream_with_context(generate()), headers=headers)

    except Exception as e:
        return f"<h3 style='text-align:center; margin-top:50px;'>Error: {str(e)}</h3><br><center><a href='/'>Go Back</a></center>", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
