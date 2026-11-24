from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, col, select

from dependencies import CurrentUser, SessionDep, get_user_or_404
from models import Follow, Like, Post, PostPublic, User, UserProfile, UserPublic

router = APIRouter(prefix="/users", tags=["users"])

# ═══════════════ Perfil con contadores ═══════════════
def to_profile(db: Session, user: User) -> UserProfile:
    # Dos conteos en direcciones OPUESTAS sobre la misma tabla:
    followers = db.exec(
        select(func.count()).select_from(Follow).where(Follow.followed_id == user.id)
    ).one()  # filas donde user es el SEGUIDO
    following = db.exec(
        select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)
    ).one()  # filas donde user es el SEGUIDOR
    return UserProfile.model_validate(
        user, update={"followers_count": followers, "following_count": following}
    )


@router.get("/{user_id}", response_model=UserPublic)
def read_user(user_id: int, db: SessionDep):
    return get_user_or_404(db, user_id)


@router.get("/{user_id}/posts", response_model=list[PostPublic])
def read_user_posts(user_id: int, db: SessionDep):
    return get_user_or_404(db, user_id).posts

@router.get("/{user_id}/likes", response_model=list[PostPublic])
def read_user_likes(
    user_id: int, db: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 20
):
    """Los posts a los que este usuario le dio like (el más reciente primero)."""
    get_user_or_404(db, user_id)
    stmt = (
        select(Post)
        .join(Like, col(Like.post_id) == col(Post.id))
        .where(Like.user_id == user_id)
        .order_by(col(Like.created_at).desc())
        .offset(offset)
        .limit(limit)
    )
    return db.exec(stmt).all()