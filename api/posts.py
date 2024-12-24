from fastapi import Depends, HTTPException, APIRouter, File, UploadFile, Form
from sqlalchemy.orm import Session
from db import schemas, get_db, models
import api.auth as auth
import base64
from sqlalchemy import func, case

router = APIRouter()  # create an instance of the APIRouter class


# create a new post
@router.post("/posts", response_model=schemas.PostResponse)
def create_post(
    caption: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    
    # read the image as binary data
    image_data = image.file.read()

    # create a new post instance
    new_post = models.Posts(
        user_id=current_user,
        caption=caption,
        image=image_data,
    )

    # add and commit the post to the database
    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)

        return {
            "id": new_post.id,
            "user_id": new_post.user_id,
            "caption": new_post.caption,
            "created_at": new_post.created_at,
            "image": base64.b64encode(new_post.image).decode("utf-8"),  #encode the image as base64
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create post: {str(e)}")


#read all posts information
@router.get("/posts", response_model=list[schemas.PostResponse])
def read_posts(db: Session = Depends(get_db)):
    posts = (
        db.query(
            models.Posts.id,
            models.Posts.user_id,
            models.Posts.caption,
            models.Posts.created_at,
            func.count(
                case([(models.PostReactions.reaction_type == "like", 1)])
            ).label("likes_count"),
            func.count(
                case([(models.PostReactions.reaction_type == "dislike", 1)])
            ).label("dislikes_count"),
        )
        .outerjoin(models.PostReactions, models.PostReactions.post_id == models.Posts.id)
        .group_by(models.Posts.id)
        .all()
    )

    # Map query results to response model
    return [
        {
            "id": post.id,
            "user_id": post.user_id,
            "caption": post.caption,
            "likes_count": post.likes_count,
            "dislikes_count": post.dislikes_count,
            "created_at": post.created_at,
        }
        for post in posts
    ]


#read post information by post_id
@router.get("/posts/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):

    # Get the post by ID
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()

    # Check if post exists
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Count likes and dislikes for the post
    likes_count = db.query(func.count(models.PostReactions.id)).filter(
        models.PostReactions.post_id == post.id,
        models.PostReactions.reaction_type == "like"
    ).scalar()

    dislikes_count = db.query(func.count(models.PostReactions.id)).filter(
        models.PostReactions.post_id == post.id,
        models.PostReactions.reaction_type == "dislike"
    ).scalar()

    # Return the response
    return {
        "id": post.id,
        "user_id": post.user_id,
        "caption": post.caption,
        "likes_count": likes_count,
        "dislikes_count": dislikes_count,
        "created_at": post.created_at,
    }

# read all posts information by a user
@router.get("/users/{user_id}/posts", response_model=list[schemas.PostResponse])
def read_user_posts(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: int = Depends(auth.decode_jwt)
):
    # check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Query posts with aggregated likes and dislikes count
    posts = (
        db.query(
            models.Posts.id,
            models.Posts.user_id,
            models.Posts.caption,
            models.Posts.created_at,
            func.count(
                case([(models.PostReactions.reaction_type == "like", 1)])
            ).label("likes_count"),
            func.count(
                case([(models.PostReactions.reaction_type == "dislike", 1)])
            ).label("dislikes_count"),
        )\
        .filter(models.Posts.user_id == user_id)
        .outerjoin(models.PostReactions, models.PostReactions.post_id == models.Posts.id)
        .group_by(models.Posts.id)
        .all()
    )

    return [
        {
            "id": post.id,
            "user_id": post.user_id,
            "caption": post.caption,
            "likes_count": post.likes_count,
            "dislikes_count": post.dislikes_count,
            "created_at": post.created_at,
        }
        for post in posts
    ]


# update a post by id
@router.put("/posts/{post_id}", response_model=schemas.PostResponse)
def update_post(
    post_id: int,
    post: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # get the post by id
    post_db = db.query(models.Posts).filter(models.Posts.id == post_id).first()

    # check if post exists
    if not post_db:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user is the owner of the post
    if post_db.user_id != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of this post"
        )
    

    # update the post
    try:
        post_db.caption = post.caption
        db.commit()
        db.refresh(post_db)

        return post_db

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update post: {str(e)}")


# delete a post by id
@router.delete("/posts/{post_id}", status_code=200)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # get the post by id
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user is the owner of the post
    if post.user_id != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of this post"
        )

    # delete the post
    try:
        db.delete(post)
        db.commit()
        return {"detail": "Post deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete post: {str(e)}")


# like and unlike a post
@router.post("/posts/{post_id}/like", response_model=schemas.PostReactionResponse)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has liked the post
    like = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "like",
        )
        .first()
    )

    # unlike the post if the user has liked it
    if like:
        try:
            response = schemas.PostReactionResponse(
                id=like.id,
                user_id=like.user_id, 
                post_id=like.post_id,
                message="Post unliked successfully"
            )
            db.delete(like)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to unlike post: {str(e)}"
            )

    # like the post if the user has not liked it
    new_like = models.PostReactions(user_id=current_user, post_id=post_id, reaction_type="like")

    try:
        response = schemas.PostReactionResponse(
            id=like.id,
            user_id=like.user_id, 
            post_id=like.post_id,
            message="Post liked successfully"
        )
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to like post: {str(e)}")

# dislike and remove dislike
@router.post("/posts/{post_id}/dislike", response_model=schemas.PostLikeResponse)
def toggle_dislike(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has disliked the post
    like = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "dislike",
        )
        .first()
    )

    # undo the dislike if the user has liked it
    if like:
        try:
            response = schemas.PostReactionResponse(
                id=like.id,
                user_id=like.user_id, 
                post_id=like.post_id,
                message="Dislike removed successfully"
            )
            db.delete(like)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to remove dislike: {str(e)}"
            )

    # like the post if the user has not liked it
    new_like = models.PostReactions(user_id=current_user, post_id=post_id, reaction_type="dislike")

    try:
        response = schemas.PostReactionResponse(
            id=like.id,
            user_id=like.user_id, 
            post_id=like.post_id,
            message="Post disliked successfully"
        )
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to like post: {str(e)}")
    
# display all likes for a post
@router.get("/posts/{post_id}/likes", response_model=list[schemas.PostReactionResponse])
def read_post_likes(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all likes for a post
    likes = db.query(models.PostReactions).filter(
        models.PostReactions.post_id == post_id,
        models.PostReactions.reaction_type == "like"
        ).all()
    return likes

# display all dislikes for a post
@router.get("/posts/{post_id}/dislikes", response_model=list[schemas.PostReactionResponse])
def read_post_dislikes(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all likes for a post
    dislikes = db.query(models.PostReactions).filter(
        models.PostReactions.post_id == post_id,
        models.PostReactions.reaction_type == "dislike"
        ).all()
    return dislikes


# count the number of likes for a post
@router.get("/posts/{post_id}/likes/count", response_model=int)
def count_post_likes(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # count the number of likes for a post
    count = (
        db.query(models.PostReactions).filter(
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "like"
            ).count()
    )
    return count

# count the number of dislikes for a post
@router.get("/posts/{post_id}/dislikes/count", response_model=int)
def count_post_dislikes(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # count the number of likes for a post
    count = (
        db.query(models.PostReactions).filter(
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "dislike"
            ).count()
    )
    return count



# check if a user has liked a post
@router.get("/posts/{post_id}/like", response_model=bool)
def check_user_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has liked the post
    like = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "like"
        )
        .first()
    )
    if like:
        return True
    return False

# check if a user has disliked a post
@router.get("/posts/{post_id}/dislike", response_model=bool)
def check_user_dislike(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has liked the post
    dislike = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "dislike"
        )
        .first()
    )
    if dislike:
        return True
    return False


# read all users who liked a post
@router.get("/posts/{post_id}/likedby", response_model=list[schemas.UserResponse])
def read_post_likedby(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all users who liked a post
    users = (
        db.query(models.User)
        .join(models.PostReactions)
        .filter(models.PostReactions.post_id == post_id,
                models.PostReactions.reaction_type == "like"
                )
        .all()
    )
    return users
   

# read all users who disliked a post
@router.get("/posts/{post_id}/dislikedby", response_model=list[schemas.UserResponse])
def read_post_dislikedby(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all users who liked a post
    users = (
        db.query(models.User)
        .join(models.PostReactions)
        .filter(models.PostReactions.post_id == post_id,
                models.PostReactions.reaction_type == "dislike"
                )
        .all()
    )
    return users
   

