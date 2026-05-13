# Video Downloader API

A powerful FastAPI-based video downloader supporting YouTube, Facebook, Pinterest, TikTok, and more. Built with `yt-dlp` for reliable video extraction.

## Features

- **Multi-Platform Support**: YouTube, Facebook, Pinterest, TikTok, and 1000+ other sites
- **Quality Selection**: Choose from best, worst, 1080p, 720p, 480p, 360p, 4k, 2k
- **Format Options**: Download as MP4 (video) or MP3 (audio only)
- **Video Info**: Get metadata without downloading
- **Format Listing**: View available formats before downloading
- **Auto Cleanup**: Automatic file cleanup after download
- **Production Ready**: Deploy on Railway, Heroku, or any cloud platform

## API Endpoints

### `GET /`
Get API information and available endpoints.

### `GET /health`
Health check endpoint for monitoring.

### `POST /download`
Download video/audio from supported platforms.

**Request Body:**
```json
{
  "url": "https://example.com/video",
  "format": "mp4",
  "quality": "best"
}
```

**Parameters:**
- `url` (required): Video URL
- `format` (optional): "mp4" or "mp3" (default: "mp4")
- `quality` (optional): "best", "worst", "1080p", "720p", "480p", "360p", "4k", "2k" (default: "best")

**Response:**
```json
{
  "success": true,
  "message": "Download successful",
  "data": {
    "title": "Video Title",
    "duration": 180,
    "thumbnail": "https://...",
    "uploader": "Channel Name",
    "format": "mp4",
    "quality": "best",
    "filename": "Video_Title.mp4"
  }
}
```

### `GET /info`
Get video information without downloading.

**Query Parameters:**
- `url` (required): Video URL

**Example:**
```bash
curl "http://localhost:8000/info?url=https://youtube.com/watch?v=VIDEO_ID"
```

### `GET /formats`
Get available video/audio formats for a URL.

**Query Parameters:**
- `url` (required): Video URL

**Example:**
```bash
curl "http://localhost:8000/formats?url=https://youtube.com/watch?v=VIDEO_ID"
```

### `DELETE /cleanup`
Manually cleanup downloaded files.

## Supported Platforms

- YouTube
- Facebook
- Pinterest
- TikTok
- Instagram
- Twitter/X
- Vimeo
- Dailymotion
- And 1000+ more sites via yt-dlp

## Local Development

### Prerequisites

- Python 3.9+
- FFmpeg (required for audio conversion and video merging)
- pip

### Installation

1. **Install FFmpeg:**

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update && sudo apt-get install -y ffmpeg
   ```

   **macOS:**
   ```bash
   brew install ffmpeg
   ```

   **Windows:**
   Download from https://ffmpeg.org/download.html

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the API:**
   - API Root: http://localhost:8000
   - Health Check: http://localhost:8000/health
   - Interactive Docs: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc

## Deployment on Railway

### Option 1: Deploy from GitHub

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect the Python project
6. Add environment variables if needed
7. Click "Deploy"

### Option 2: Deploy with Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Initialize and deploy:**
   ```bash
   railway init
   railway up
   ```

### Railway Configuration

The app includes:
- `Procfile` - Defines the web process for Railway
- `requirements.txt` - Python dependencies
- Automatic port detection via `$PORT` environment variable

No additional configuration needed!

### Environment Variables (Optional)

- `PORT` - Automatically set by Railway
- `LOG_LEVEL` - Set logging level (default: INFO)

## Usage Examples

### Using cURL

**Download MP4 video (best quality):**
```bash
curl -X POST "http://localhost:8000/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=VIDEO_ID", "format": "mp4", "quality": "best"}'
```

**Download MP3 audio:**
```bash
curl -X POST "http://localhost:8000/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=VIDEO_ID", "format": "mp3"}'
```

**Download 720p video:**
```bash
curl -X POST "http://localhost:8000/download" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=VIDEO_ID", "format": "mp4", "quality": "720p"}'
```

**Get video info:**
```bash
curl "http://localhost:8000/info?url=https://youtube.com/watch?v=VIDEO_ID"
```

**List available formats:**
```bash
curl "http://localhost:8000/formats?url=https://youtube.com/watch?v=VIDEO_ID"
```

### Using Python

```python
import requests

# Download video
response = requests.post(
    "http://localhost:8000/download",
    json={
        "url": "https://youtube.com/watch?v=VIDEO_ID",
        "format": "mp4",
        "quality": "1080p"
    }
)
print(response.json())

# Get video info
response = requests.get(
    "http://localhost:8000/info",
    params={"url": "https://youtube.com/watch?v=VIDEO_ID"}
)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
// Download video
const response = await fetch('http://localhost:8000/download', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    url: 'https://youtube.com/watch?v=VIDEO_ID',
    format: 'mp4',
    quality: 'best'
  })
});

const data = await response.json();
console.log(data);
```

## Quality Options

| Quality | Description |
|---------|-------------|
| `best` | Best available quality (default) |
| `worst` | Lowest available quality |
| `4k` | 2160p resolution |
| `2k` | 1440p resolution |
| `1080p` | Full HD |
| `720p` | HD |
| `480p` | Standard Definition |
| `360p` | Low Quality |

## Important Notes

### YouTube Restrictions
- Some videos may require authentication
- Age-restricted videos may not be accessible
- Private/unlisted videos require proper cookies
- Rate limiting may apply for frequent requests

### Legal Considerations
- Only download content you have rights to
- Respect copyright and terms of service
- This tool is for personal/educational use

### Performance
- Large videos may take time to process
- Files are automatically cleaned up after response
- Consider implementing queue system for production

## Troubleshooting

### "Requested format is not available"
- Try a different quality setting
- Some videos don't have all quality options
- Use `/formats` endpoint to see available formats

### "Sign in to confirm you're not a bot"
- YouTube has bot detection
- For production, consider using cookies or proxies
- Some videos may not be accessible programmatically

### FFmpeg errors
- Ensure FFmpeg is installed and in PATH
- Required for MP3 conversion and video merging

## File Structure

```
/workspace
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Procfile            # Railway deployment config
├── README.md           # This file
└── downloads/          # Temporary download directory
```

## License

MIT License - Feel free to use and modify

## Support

For issues related to:
- **yt-dlp**: https://github.com/yt-dlp/yt-dlp
- **FastAPI**: https://github.com/tiangolo/fastapi
- **This project**: Create an issue on GitHub

---

**Built with FastAPI and yt-dlp** 🚀
