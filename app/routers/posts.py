from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_async_session
from app.models import User, Post, FileType
from app.schemas import PostCreate, PostResponse, PostList
from app.auth import current_active_user
from typing import List
import uuid
import aiofiles
import os
from pathlib import Path
from app.config import settings

# What: Create router for post endpoints
# Why: Groups all post-related routes together
# How: FastAPI Router with /posts prefix (set in main.py)
router = APIRouter()

# What: Helper function to determine file type
# Why: Need to know if uploaded file is image or video
# How: Check file extension
def get_file_type(filename: str) -> FileType:
    """
    What: Determines if file is image or video
    Why: Store correct type in database
    How: Checks file extension
    """
    ext = Path(filename).suffix.lower()
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv'}
    
    if ext in image_extensions:
        return FileType.IMAGE
    elif ext in video_extensions:
        return FileType.VIDEO
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}"
        )

# What: Helper to save uploaded file
# Why: Store file to disk asynchronously
# How: Uses aiofiles for non-blocking I/O
async def save_upload_file(upload_file: UploadFile, destination: Path):
    """
    What: Saves uploaded file to disk
    Why: Persist media files locally
    How: Async file writing with aiofiles
    
    Args:
        upload_file: File from request
        destination: Where to save it
    """
    async with aiofiles.open(destination, 'wb') as out_file:
        # What: Read file in chunks
        # Why: Memory efficient for large videos
        # How: 1MB chunks
        while content := await upload_file.read(1024 * 1024):  # 1MB chunks
            await out_file.write(content)

# ============================================
# ENDPOINT 1: UPLOAD POST
# ============================================

@router.post("/upload", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def upload_post(
    file: UploadFile = File(...),  # What: Uploaded file (required)
    caption: str = Form(None),      # What: Optional caption from form data
    session: AsyncSession = Depends(get_async_session),  # What: Database session
    user: User = Depends(current_active_user)  # What: Current logged-in user (JWT)
):
    """
    What: Upload a photo or video with optional caption
    Why: Core feature - users share content
    How: 
        1. Validate file type
        2. Save file to disk
        3. Create database entry
        4. Return post details
    
    Security: Requires authentication (current_active_user)
    """
    
    # What: Validate file size
    # Why: Prevent huge uploads (DoS protection)
    # How: Check content length
    file_size = 0
    for chunk in iter(lambda: file.file.read(1024 * 1024), b''):
        file_size += len(chunk)
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
    file.file.seek(0)  # Reset file pointer to beginning
    
    # What: Validate file extension
    # Why: Only allow images and videos
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # What: Generate unique filename
    # Why: Prevent overwrites, avoid name collisions
    # How: UUID + original extension
    file_id = uuid.uuid4()
    filename = f"{file_id}{file_ext}"
    file_path = Path(settings.UPLOAD_DIR) / filename
    
    # What: Ensure upload directory exists
    # Why: Might not exist on first run
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # What: Save file to disk
    # Why: Persist the uploaded media
    try:
        await save_upload_file(file, file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # What: Determine file type (image or video)
    file_type = get_file_type(file.filename)
    
    # What: Create database entry
    # Why: Track post metadata
    # How: SQLAlchemy model
    new_post = Post(
        caption=caption,
        url=f"/{settings.UPLOAD_DIR}/{filename}",  # Relative URL path
        file_type=file_type,
        user_id=user.id
    )
    
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)  # Get generated fields (id, created_at)
    
    # What: Load user relationship
    # Why: Need user.email for response
    # How: Eager loading with selectinload
    await session.refresh(new_post, ["user"])
    
    # What: Return response
    # Why: Confirm upload success with details
    return PostResponse(
        id=new_post.id,
        caption=new_post.caption,
        url=new_post.url,
        file_type=new_post.file_type,
        created_at=new_post.created_at,
        user_id=new_post.user_id,
        user_email=new_post.user.email,
        is_owner=True  # Uploader is always owner
    )

# ============================================
# ENDPOINT 2: GET FEED (All Posts)
# ============================================

@router.get("/feed", response_model=List[PostList])
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
    limit: int = 50,  # What: Max posts to return
    offset: int = 0   # What: Pagination offset
):
    """
    What: Get chronological feed of all posts
    Why: Main browsing feature (like Instagram feed)
    How:
        1. Query all posts with user info
        2. Order by newest first
        3. Add is_owner flag for each post
    
    Security: Requires authentication
    """
    
    # What: Query posts with user relationship
    # Why: Need user email for each post
    # How: JOIN users table, eager load with selectinload
    query = (
        select(Post)
        .options(selectinload(Post.user))  # What: Eager load user data (avoid N+1 queries)
        .order_by(Post.created_at.desc())  # What: Newest first
        .limit(limit)
        .offset(offset)
    )
    
    result = await session.execute(query)
    posts = result.scalars().all()
    
    # What: Build response with is_owner flag
    # Why: Frontend needs to know if current user owns each post
    # How: Compare post.user_id with current user.id
    response = []
    for post in posts:
        response.append(PostList(
            id=post.id,
            caption=post.caption,
            url=post.url,
            file_type=post.file_type,
            created_at=post.created_at,
            user_id=post.user_id,
            user_email=post.user.email,
            is_owner=(post.user_id == user.id)  # What: True if current user created this post
        ))
    
    return response

# ============================================
# ENDPOINT 3: GET SINGLE POST
# ============================================

@router.get("/post/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: uuid.UUID,  # What: Post ID from URL path
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """
    What: Get details of a specific post
    Why: View individual post (sharing links, etc.)
    How: Query by ID, include user info
    
    Security: Requires authentication
    """
    
    # What: Query post by ID with user relationship
    query = select(Post).options(selectinload(Post.user)).where(Post.id == post_id)
    result = await session.execute(query)
    post = result.scalar_one_or_none()
    
    # What: Handle post not found
    # Why: Return 404 instead of server error
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    # What: Return post details
    return PostResponse(
        id=post.id,
        caption=post.caption,
        url=post.url,
        file_type=post.file_type,
        created_at=post.created_at,
        user_id=post.user_id,
        user_email=post.user.email,
        is_owner=(post.user_id == user.id)
    )

# ============================================
# ENDPOINT 4: DELETE POST
# ============================================

@router.delete("/post/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    """
    What: Delete a post (and its file)
    Why: Users can remove their own content
    How:
        1. Find post
        2. Verify ownership
        3. Delete file from disk
        4. Delete database entry
    
    Security: Only owner can delete their post
    """
    
    # What: Find post
    query = select(Post).where(Post.id == post_id)
    result = await session.execute(query)
    post = result.scalar_one_or_none()
    
    # What: Handle not found
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    # What: Verify ownership
    # Why: Users can only delete their own posts (authorization)
    if post.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this post"
        )
    
    # What: Delete file from disk
    # Why: Free up storage space
    # How: Remove file if exists
    file_path = Path(post.url.lstrip('/'))  # Remove leading /
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete file: {e}")
            # Continue anyway - database consistency more important
    
    # What: Delete from database
    await session.delete(post)
    await session.commit()
    
    # What: Return 204 No Content (successful deletion)
    # Why: Standard REST pattern for DELETE
    return None
