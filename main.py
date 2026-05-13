from fastapi import FastAPI, HTTPException, BackgroundTasks, Response, Request
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
import yt_dlp
import os
import uuid
from pathlib import Path
import logging
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Railway Video Downloader",
    description="Download videos from YouTube, Facebook, Pinterest, and TikTok optimized for Railway deployment",
    version="1.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create temp directory for downloads
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)


class DownloadRequest(BaseModel):
    url: str
    format: str = "mp4"  # mp4 or mp3
    quality: Optional[str] = "best"  # best, worst, 1080p, 720p, etc.


class FormatInfo(BaseModel):
    format_id: str
    resolution: str
    filesize: Optional[int]
    vcodec: str
    acodec: str
    ext: str


@app.get("/")
async def root(request: Request):
    """Serve the frontend HTML interface"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api-info")
async def api_info():
    """API information endpoint"""
    return {
        "service": "Railway Video Downloader",
        "platform": "railway.app",
        "status": "running",
        "endpoints": {
            "/download": "POST - Download video/audio",
            "/info": "GET - Get video information",
            "/formats": "POST - Get available formats",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "platform": "railway"}


def get_quality_filter(quality: str) -> str:
    """Convert quality string to yt-dlp format filter"""
    if quality == "best":
        return "bestvideo[ext!=webm]+bestaudio/best"
    elif quality == "worst":
        return "worstvideo+worstaudio/worst"
    elif quality.endswith("p"):
        # e.g., 1080p, 720p
        height = quality[:-1]
        return f"bestvideo[height<={height}][ext!=webm]+bestaudio/best[height<={height}]"
    elif quality.endswith("k"):
        # e.g., 4k, 2k
        height_map = {"4k": "2160", "2k": "1440"}
        height = height_map.get(quality.lower(), "1080")
        return f"bestvideo[height<={height}][ext!=webm]+bestaudio/best[height<={height}]"
    else:
        return "bestvideo[ext!=webm]+bestaudio/best"


def download_video(url: str, output_path: str, format_type: str, quality: str) -> dict:
    """Download video using yt-dlp"""
    
    # Common options for all downloads
    common_opts = {
        'outtmpl': output_path + '.%(ext)s',
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'ignoreerrors': False,
        'retries': 3,
        'fragment_retries': 3,
        # Add user-agent and headers to avoid blocking
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        # Extractor arguments for specific platforms - bypass bot detection
        'extractor_args': {
            'facebook': {
                'prefer_embedded': ['True'],
            },
            'youtube': {
                'player_client': ['web', 'android'],
                'skip': ['hls', 'dash'],
            },
        },
    }
    
    ydl_opts = common_opts.copy()
    
    if format_type == "mp3":
        ydl_opts.update({
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:  # mp4
        quality_filter = get_quality_filter(quality)
        ydl_opts.update({
            'format': quality_filter,
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
        })
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Get the actual downloaded file path
            if format_type == "mp3":
                downloaded_file = output_path + '.mp3'
            else:
                # Try multiple possible extensions
                for ext in ['.mp4', '.mkv', '.webm']:
                    downloaded_file = output_path + ext
                    if os.path.exists(downloaded_file):
                        break
                else:
                    downloaded_file = output_path + '.mp4'
            
            if not os.path.exists(downloaded_file):
                # Fallback: search for any file with the unique_id
                for f in DOWNLOAD_DIR.glob(f"{output_path.split('/')[-1]}*"):
                    if f.suffix in ['.mp4', '.mkv', '.webm', '.mp3']:
                        downloaded_file = str(f)
                        break
            
            return {
                "success": True,
                "file_path": downloaded_file,
                "title": info.get('title', 'Unknown'),
                "duration": info.get('duration', 0),
                "thumbnail": info.get('thumbnail', ''),
                "uploader": info.get('uploader', 'Unknown')
            }
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise Exception(f"Download failed: {str(e)}")


@app.post("/download")
async def download_endpoint(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Download video/audio from supported platforms and return the file
    
    Supported platforms: YouTube, Facebook, Pinterest, TikTok
    Returns the actual video/audio file for download
    """
    try:
        # Validate URL
        if not request.url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # Validate format
        if request.format not in ["mp4", "mp3"]:
            raise HTTPException(status_code=400, detail="Format must be 'mp4' or 'mp3'")
        
        # Generate unique filename
        unique_id = str(uuid.uuid4())
        output_template = str(DOWNLOAD_DIR / f"{unique_id}")
        
        # Download the video
        logger.info(f"Starting download: {request.url}, format: {request.format}, quality: {request.quality}")
        
        result = download_video(
            url=request.url,
            output_path=output_template,
            format_type=request.format,
            quality=request.quality
        )
        
        downloaded_file = result["file_path"]
        
        if not os.path.exists(downloaded_file):
            raise HTTPException(status_code=500, detail="File was not created")
        
        # Determine filename for download
        ext = ".mp3" if request.format == "mp3" else ".mp4"
        safe_title = "".join(c for c in result["title"] if c.isalnum() or c in " -_").strip()[:50]
        filename = f"{safe_title}{ext}"
        
        # Get file size
        file_size = os.path.getsize(downloaded_file)
        
        # Schedule cleanup after response is sent
        def cleanup():
            try:
                import time
                time.sleep(2)  # Wait a bit to ensure file is fully sent
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                # Clean up any related files
                for f in DOWNLOAD_DIR.glob(f"{unique_id}*"):
                    if os.path.exists(f):
                        os.remove(f)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
        
        background_tasks.add_task(cleanup)
        
        # Return the actual file as a streaming response
        def iterfile():
            with open(downloaded_file, mode="rb") as file_like:
                yield from file_like
        
        media_type = "audio/mpeg" if request.format == "mp3" else "video/mp4"
        
        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Title": result["title"],
                "X-Duration": str(result["duration"]),
                "X-Uploader": result["uploader"],
                "X-File-Size": str(file_size)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
async def get_video_info(url: str):
    """
    Get video information without downloading
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'best',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android'],
                },
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if not info:
                raise HTTPException(status_code=404, detail="Video information not found")
            
            return {
                "success": True,
                "data": {
                    "title": info.get('title', 'Unknown'),
                    "description": (info.get('description') or '')[:500],
                    "duration": info.get('duration', 0),
                    "thumbnail": info.get('thumbnail', ''),
                    "uploader": info.get('uploader', 'Unknown'),
                    "upload_date": info.get('upload_date', ''),
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0),
                    "platform": info.get('extractor', 'Unknown'),
                    "url": info.get('webpage_url', url)
                }
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Info endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/formats")
async def get_available_formats(request: DownloadRequest):
    """
    Get available video/audio formats for a URL
    """
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            if not info:
                raise HTTPException(status_code=404, detail="Video information not found")
            
            formats = []
            for fmt in info.get('formats', []):
                if fmt:
                    formats.append({
                        "format_id": fmt.get('format_id', ''),
                        "resolution": fmt.get('resolution', str(fmt.get('height', 'N/A'))),
                        "filesize": fmt.get('filesize'),
                        "vcodec": fmt.get('vcodec', 'none'),
                        "acodec": fmt.get('acodec', 'none'),
                        "ext": fmt.get('ext', ''),
                        "quality": fmt.get('quality', 0),
                        "height": fmt.get('height')
                    })
            
            # Sort by quality (handle None values)
            formats.sort(key=lambda x: (x.get('quality') or 0), reverse=True)
            
            return {
                "success": True,
                "title": info.get('title', 'Unknown'),
                "duration": info.get('duration', 0),
                "thumbnail": info.get('thumbnail', ''),
                "uploader": info.get('uploader', 'Unknown'),
                "formats": formats[:30],  # Limit to top 30 formats
                "recommended_qualities": ["best", "1080p", "720p", "480p", "360p"]
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Formats endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cleanup")
async def cleanup_downloads():
    """Manual cleanup of download directory"""
    try:
        count = 0
        for file in DOWNLOAD_DIR.glob("*"):
            try:
                file.unlink()
                count += 1
            except Exception as e:
                logger.error(f"Error deleting {file}: {e}")
        
        return {"success": True, "message": f"Cleaned up {count} files"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # Railway sets PORT environment variable
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
