from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_async_session
from app.models import User, Post, FileType
from app.schemas import PostCreate, PostResponse, PostList
from app.auth import current_active_user
# What: Import List and Optional for Python 3.9 compatibility
from typing import List, Optional
import uuid
import aiofiles
import os
from pathlib import Path
from app.config import settings

router = APIRouter()

def get_file_type(filename: str) -> FileType:
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

async def save_upload_file(upload_file: UploadFile, destination: Path):
    async with aiofiles.open(destination, 'wb') as out_file:
        while content := await upload_file.read(1024 * 1024):
            await out_file.write(content)

@router.post("/upload", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def upload_post(
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),  # ← Changed from str | None
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    file_size = 0
    for chunk in iter(lambda: file.file.read(1024 * 1024), b''):
        file_size += len(chunk)
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )
    file.file.seek(0)
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    file_id = uuid.uuid4()
    filename = f"{file_id}{file_ext}"
    file_path = Path(settings.UPLOAD_DIR) / filename
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    try:
        await save_upload_file(file, file_path)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    file_type = get_file_type(file.filename)
    
    new_post = Post(
        caption=caption,
        url=f"/{settings.UPLOAD_DIR}/{filename}",
        file_type=file_type,
        user_id=user.id
    )
    
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    await session.refresh(new_post, ["user"])
    
    return PostResponse(
        id=new_post.id,
        caption=new_post.caption,
        url=new_post.url,
        file_type=new_post.file_type,
        created_at=new_post.created_at,
        user_id=new_post.user_id,
        user_email=new_post.user.email,
        is_owner=True
    )

@router.get("/feed", response_model=List[PostList])  # ← List instead of list
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
    limit: int = 50,
    offset: int = 0
):
    query = (
        select(Post)
        .options(selectinload(Post.user))
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    
    result = await session.execute(query)
    posts = result.scalars().all()
    
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
            is_owner=(post.user_id == user.id)
        ))
    
    return response

@router.get("/post/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    query = select(Post).options(selectinload(Post.user)).where(Post.id == post_id)
    result = await session.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
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

@router.delete("/post/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    query = select(Post).where(Post.id == post_id)
    result = await session.execute(query)
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )
    
    if post.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this post"
        )
    
    file_path = Path(post.url.lstrip('/'))
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Failed to delete file: {e}")
    
    await session.delete(post)
    await session.commit()
    return None